#!/usr/bin/env python3
"""Store calldata."""
import sys
from solana.rpc.api import Client
from solders.keypair import Keypair  
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM
import base64

PROG = "EiNHPv89CvbRLF5ioYAHqGNvrPPXZUEiLkGUBVfbJxto"

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 calldata.py <data>")
        print("  data: data to write (text or base64:...)")
        sys.exit(1)
    
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROG)
    
    data = sys.argv[1]
    
    if data.startswith("base64:"):
        data = base64.b64decode(data[7:])
    else:
        data = data.encode()
    
    # Use payer account as target
    calldata_ix = Instruction(
        program_id=prog,
        accounts=[
            AM(pubkey=payer, is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=False),
        ],
        data=bytes([3]) + data,
    )
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([calldata_ix], payer, blockhash)
    txn = Transaction([kp], msg, blockhash)
    result = client.send_transaction(txn)
    print(f"Written: {result.value}")

if __name__ == "__main__":
    main()