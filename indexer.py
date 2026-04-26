#!/usr/bin/env python3
import asyncio
import json
import base58
import struct
import re
import aiohttp

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.rpc import websocket_api as ws
from solders.pubkey import Pubkey
from solders.signature import Signature
from setting import PROGRAM_ID

RPC_URL = "http://localhost:8899"
WS_URL = "ws://localhost:8900"
SERVER_URL = "http://localhost:3000"

print(f"--- Indexer Active: Monitoring {PROGRAM_ID} ---")

def parse_instruction(data: bytes, accounts: list) -> dict:
    if not data: return {"error": "no data"}
    opcode = data[0]
    result = {"opcode": opcode}
    
    # 尝试提取金额 (u64, 8 bytes)
    amount = None
    if len(data) >= 9:
        amount = struct.unpack("<Q", data[1:9])[0]
        result["amount"] = amount

    if opcode == 0: 
        result["name"] = "initialize_vault"
    elif opcode == 1: 
        result["name"] = "lock"
        # lock(accounts): [source_ata, vault_ata, user_payer, token_program]
        if len(accounts) >= 3:
            result["sender"] = accounts[2]
    elif opcode == 2: 
        result["name"] = "release"
        # release(accounts): [vault_state, vault_ata, dest_ata, operator, token_program]
        if len(accounts) >= 4:
            result["sender"] = accounts[3]
    elif opcode == 3:
        result["name"] = "calldata"
        payload = data[1:]
        result["text"] = payload.decode('utf-8', errors='replace')
    return result

class Indexer:
    def __init__(self):
        self.client = Client(RPC_URL)
        self.prog = PROGRAM_ID
        self.processed_signatures = set()
        self.http_session = None
        print("Connected to RPC. Waiting for events...")

    async def send_to_server(self, data):
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
        try:
            async with self.http_session.post(
                f"{SERVER_URL}/",
                json=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                result = await resp.json()
                print(f"  📤 Server response: {result}")
                return result
        except Exception as e:
            print(f"  ❌ Server error: {e}")
            return None

    async def close(self):
        if self.http_session:
            await self.http_session.close()

    def process_transaction(self, signature_str):
        try:
            resp = self.client.get_transaction(
                Signature.from_string(signature_str),
                encoding="jsonParsed",
                commitment=Confirmed
            )
        except Exception as e:
            print(f"  ❌ Fetch error: {e}")
            return

        if not resp.value:
            print(f"  ❌ Transaction not found: {signature_str}")
            return

        txn_dict = json.loads(resp.value.to_json())
        meta = txn_dict.get('meta', {})
        block_time = meta.get('blockTime')
        slot = meta.get('slot')

        account_keys = txn_dict.get('transaction', {}).get('message', {}).get('accountKeys', [])
        pubkeys_list = [a.get('pubkey') if isinstance(a, dict) else a for a in account_keys]
        signers = [a.get('pubkey') for a in account_keys if (a.get('signer') if isinstance(a, dict) else False)]

        all_ixs = (
            txn_dict.get('transaction', {}).get('message', {}).get('instructions', []) +
            sum((g.get('instructions', []) for g in meta.get('innerInstructions', [])), [])
        )

        for ix in all_ixs:
            if ix.get('programId') != self.prog:
                continue

            raw_data = ix.get('data')
            if not raw_data:
                continue

            try:
                data_bytes = base58.b58decode(raw_data)
                ix_accounts = ix.get('accounts', [])
                parsed = parse_instruction(data_bytes, ix_accounts)

                mint = None
                token_balances = meta.get('postTokenBalances', [])
                involved_set = set(ix_accounts)
                for balance in token_balances:
                    idx = balance.get('accountIndex')
                    if idx and idx < len(pubkeys_list) and pubkeys_list[idx] in involved_set:
                        mint = balance.get('mint')
                        break

                if mint:
                    parsed["mint"] = mint

                parsed["block_time"] = block_time
                parsed["slot"] = slot
                parsed["sender"] = signers[0] if signers else None

                print(f"  ✨ SUCCESS: {parsed}")
                return parsed
            except Exception as e:
                print(f"  Decode Error: {e}")

        return None

    async def run(self):
        from solana.rpc.websocket_api import RpcTransactionLogsFilterMentions

        async with ws.connect(WS_URL) as ws_client:
            await ws_client.logs_subscribe(
                RpcTransactionLogsFilterMentions(Pubkey.from_string(self.prog)),
                commitment=Confirmed
            )
            print("✅ Subscribed! Monitoring activity...")

            async for msg in ws_client:
                msg_str = str(msg)
                sigs = re.findall(r'signature: "([a-zA-Z0-9]{32,})"', msg_str)
                if not sigs: sigs = re.findall(r'signature=([a-zA-Z0-9]{32,})', msg_str)

                for s in set(sigs):
                    if s in self.processed_signatures:
                        continue
                    self.processed_signatures.add(s)
                    print(f"\n🔔 Event Detected: {s}")
                    await asyncio.sleep(1.0)
                    result = self.process_transaction(s)
                    if result:
                        try:
                            call = json.loads(result.get("text", "{}"))
                            payload = {
                                "info": {
                                    "name": call.get("f"),
                                    "opcode": result.get("opcode"),
                                    "block_time": result.get("block_time"),
                                    "slot": result.get("slot"),
                                    "sender": result.get("sender"),
                                    "txhash": s,
                                },
                                "args": call.get("a", []),
                            }
                        except:
                            payload = {"info": {}, "args": []}
                        await self.send_to_server(payload)

if __name__ == "__main__":
    indexer = Indexer()
    try:
        asyncio.run(indexer.run())
    except KeyboardInterrupt:
        print("\nBye.")
    finally:
        asyncio.run(indexer.close())
