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

def parse_instruction(data: bytes) -> dict:
    if not data: return {"error": "no data"}
    opcode = data[0]
    result = {"opcode": opcode}
    if opcode == 0: result["name"] = "initialize_vault"
    elif opcode == 1: result["name"] = "lock"
    elif opcode == 2: result["name"] = "release"
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
        # 使用 jsonParsed 获取事务，并强制转为字典
        sig = Signature.from_string(signature_str)
        resp = self.client.get_transaction(sig, encoding="jsonParsed", commitment=Confirmed)
        
        if not resp.value:
            print(f"  ❌ Failed to fetch transaction details for {signature_str}")
            return

        # 将对象序列化再反序列化，得到纯字典，绕过 solders 类的属性访问限制
        txn_dict = json.loads(resp.value.to_json())
        
        # 提取所有指令
        all_ixs = []
        
        # 1. 提取外层指令
        msg = txn_dict.get('transaction', {}).get('message', {})
        all_ixs.extend(msg.get('instructions', []))
        
        # 2. 提取内层指令 (CPI)
        meta = txn_dict.get('meta', {})
        inner_groups = meta.get('innerInstructions', [])
        for group in inner_groups:
            all_ixs.extend(group.get('instructions', []))

        print(f"  Scanning {len(all_ixs)} instructions...")

        for ix in all_ixs:
            # 在 jsonParsed 模式下，自定义程序通常在 'programId' 字段
            p_id = ix.get('programId')
            if p_id == self.prog:
                # 数据在 'data' 字段，通常是 Base58 编码的字符串
                raw_data = ix.get('data')
                if raw_data:
                    print(f"  🎯 Match! Parsing data: {raw_data[:20]}...")
                    try:
                        data_bytes = base58.b58decode(raw_data)
                        parsed = parse_instruction(data_bytes)
                        print(f"  ✨ SUCCESS: {parsed}")
                        return parsed
                    except Exception as e:
                        print(f"  Decode Error: {e}")
        
        print("  ⚠️ Target program invoked, but no data-carrying instructions found.")
        return None

    async def run(self):
        from solana.rpc.websocket_api import RpcTransactionLogsFilterMentions
        
        async with ws.connect(WS_URL) as ws_client:
            await ws_client.logs_subscribe(
                RpcTransactionLogsFilterMentions(Pubkey.from_string(self.prog)), 
                commitment=Confirmed
            )
            print("✅ Subscribed! Run calldata.py now.")
            
            async for msg in ws_client:
                msg_str = str(msg)
                # 从日志中提取签名
                sigs = re.findall(r'signature: "([a-zA-Z0-9]{32,})"', msg_str)
                if not sigs: sigs = re.findall(r'signature=([a-zA-Z0-9]{32,})', msg_str)
                
                if sigs:
                    for s in set(sigs):
                        print(f"\n🔔 Event Detected: {s}")
                        # 稍微等一下让 RPC 准备好
                        await asyncio.sleep(1.2)
                        self.process_transaction(s)

if __name__ == "__main__":
    indexer = Indexer()
    try:
        asyncio.run(indexer.run())
    except KeyboardInterrupt:
        print("\nBye.")
