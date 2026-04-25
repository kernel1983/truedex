#!/usr/bin/env python3
import asyncio
import json
import base64
import base58
import struct
import sys
import re

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.rpc import websocket_api as ws
from solders.pubkey import Pubkey
from solders.signature import Signature

PROGRAM_ID = "8ZTKLtRRoji4AwAmYwguNkC1VgJszD1rdASZhxSbRLXA"
RPC_URL = "http://localhost:8899"
WS_URL = "ws://localhost:8900"

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
        print("Connected to RPC. Waiting for events...")

    def process_transaction(self, signature_str):
        sig = Signature.from_string(signature_str)
        resp = self.client.get_transaction(sig, encoding="jsonParsed", commitment=Confirmed)
        
        if not resp.value:
            print(f"  ❌ Failed to fetch transaction details for {signature_str}")
            return

        txn_dict = json.loads(resp.value.to_json())
        meta = txn_dict.get('meta', {})
        
        # 提取账户列表，用于匹配 Mint
        account_keys = txn_dict.get('transaction', {}).get('message', {}).get('accountKeys', [])
        pubkeys_list = [a.get('pubkey') if isinstance(a, dict) else a for a in account_keys]

        all_ixs = []
        msg = txn_dict.get('transaction', {}).get('message', {})
        all_ixs.extend(msg.get('instructions', []))
        
        inner_groups = meta.get('innerInstructions', [])
        for group in inner_groups:
            all_ixs.extend(group.get('instructions', []))

        for ix in all_ixs:
            p_id = ix.get('programId')
            if p_id == self.prog:
                raw_data = ix.get('data')
                ix_accounts = ix.get('accounts', [])
                if raw_data:
                    try:
                        data_bytes = base58.b58decode(raw_data)
                        parsed = parse_instruction(data_bytes, ix_accounts)
                        
                        # 尝试从 Token Balances 中匹配 Mint
                        mint = None
                        token_balances = meta.get('postTokenBalances', [])
                        involved_set = set(ix_accounts)
                        for balance in token_balances:
                            idx = balance.get('accountIndex')
                            if idx is not None and idx < len(pubkeys_list):
                                if pubkeys_list[idx] in involved_set:
                                    mint = balance.get('mint')
                                    break
                        
                        if mint:
                            parsed["mint"] = mint
                            
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
                
                if sigs:
                    for s in set(sigs):
                        print(f"\n🔔 Event Detected: {s}")
                        await asyncio.sleep(1.0) # 等待 RPC 同步
                        self.process_transaction(s)

if __name__ == "__main__":
    indexer = Indexer()
    try:
        asyncio.run(indexer.run())
    except KeyboardInterrupt:
        print("\nBye.")
