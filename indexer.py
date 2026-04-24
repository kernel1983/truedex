#!/usr/bin/env python3
"""Transaction indexer with WebSocket subscription."""
import asyncio
import json
import logging
import base64
import base58
import struct
import signal

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.rpc import websocket_api as ws
from solders.pubkey import Pubkey
import rocksdb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROGRAM_ID = "EiNHPv89CvbRLF5ioYAHqGNvrPPXZUEiLkGUBVfbJxto"
RPC_URL = "http://localhost:8899"
WS_URL = "ws://localhost:8900"

def parse_instruction(data: bytes) -> dict:
    if not data:
        return {"error": "no data"}
    
    opcode = data[0]
    result = {"opcode": opcode}
    
    if opcode == 0:
        result["name"] = "initialize_vault"
    elif opcode == 1:
        if len(data) >= 9:
            amount = struct.unpack("<Q", data[1:9])[0]
            result["name"] = "lock"
            result["amount"] = amount
    elif opcode == 2:
        if len(data) >= 9:
            amount = struct.unpack("<Q", data[1:9])[0]
            result["name"] = "release"
            result["amount"] = amount
    elif opcode == 3:
        result["name"] = "calldata"
        result["data"] = base64.b64encode(data[1:]).decode()
    
    return result

class Indexer:
    def __init__(self):
        self.client = Client(RPC_URL)
        self.prog = Pubkey.from_string(PROGRAM_ID)
        self.db = rocksdb.DB("./indexer_data", rocksdb.Options(create_if_missing=True))
        self.running = True
    
    def save(self, sig: str, data: dict):
        self.db.put(sig.encode(), json.dumps(data).encode())
        logger.info(f"Saved: {sig[:20]}...")
    
    async def fetch_historic(self, limit: int = 100):
        logger.info(f"Fetching historic transactions...")
        
        sigs = self.client.get_signatures_for_address(self.prog, limit=limit, commitment=Confirmed).value
        
        count = 0
        for sig_info in sigs:
            sig = str(sig_info.signature)
            if self.db.get(sig.encode()):
                continue
            
            txn = self.client.get_transaction(sig_info.signature, encoding="jsonParsed", commitment=Confirmed).value
            if not txn:
                continue
            
            parsed = self._process_txn(txn)
            if parsed:
                self.save(sig, parsed)
                count += 1
        
        logger.info(f"Fetched {count} historic transactions")
    
    def _process_txn(self, txn) -> dict:
        try:
            trans = txn.transaction.transaction
            msg = trans.message
            account_keys = [str(k) for k in msg.account_keys]
            
            for instr in msg.instructions:
                if str(instr.program_id) != PROGRAM_ID:
                    continue
                
                data = base58.b58decode(instr.data) if instr.data else b""
                parsed = parse_instruction(data)
                
                if parsed.get("name"):
                    parsed["accounts"] = [str(a) for a in instr.accounts]
                    return parsed
            
            return None
        except Exception as e:
            logger.error(f"Error processing: {e}")
            return None
    
    async def subscribe(self):
        logger.info(f"Subscribing to {PROGRAM_ID}...")
        
        async with ws.connect(WS_URL) as ws_client:
            await ws_client.program_subscribe(self.prog, commitment=Confirmed)
            logger.info("Subscribed!")
            
            async for msg in ws_client:
                if not self.running:
                    break
                
                try:
                    if hasattr(msg, 'ctx'):
                        slot = msg.ctx.slot
                    
                    if isinstance(msg, dict):
                        parsed = self._process_txn(msg)
                        if parsed:
                            sig = str(msg["transaction"]["signatures"][0])
                            self.save(sig, parsed)
                            
                except Exception as e:
                    logger.error(f"Error: {e}")
    
    def close(self):
        self.running = False
        logger.info("Closed")

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch historic")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    
    indexer = Indexer()
    
    if args.fetch:
        await indexer.fetch_historic(args.limit)
    
    try:
        await indexer.subscribe()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        indexer.close()

if __name__ == "__main__":
    asyncio.run(main())