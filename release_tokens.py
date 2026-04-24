#!/usr/bin/env python3
"""Release tokens from vault by operator."""
import sys
from solana.rpc.api import Client
from solders.keypair import Keypair  
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM
from spl.token.constants import TOKEN_PROGRAM_ID
import struct

PROG = "8ZTKLtRRoji4AwAmYwguNkC1VgJszD1rdASZhxSbRLXA"

def main():
    if len(sys.argv) != 5:
        print("Usage: python3 release_tokens.py <vault_state> <vault> <destination> <amount>")
        sys.exit(1)
    
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROG)
    token_prog = TOKEN_PROGRAM_ID
    
    vault_state = P.from_string(sys.argv[1])
    vault = P.from_string(sys.argv[2])
    destination = P.from_string(sys.argv[3])
    amount = int(sys.argv[4])
    
    release_ix = Instruction(
        program_id=prog,
        accounts=[
            AM(pubkey=vault_state, is_signer=False, is_writable=False),
            AM(pubkey=vault, is_signer=False, is_writable=True),
            AM(pubkey=destination, is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=False),
            AM(pubkey=token_prog, is_signer=False, is_writable=False),
        ],
        data=bytes([2]) + struct.pack("<Q", amount),
    )
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([release_ix], payer, blockhash)
    txn = Transaction([kp], msg, blockhash)
    result = client.send_transaction(txn)
    print(f"Released: {result.value}")

if __name__ == "__main__":
    main()