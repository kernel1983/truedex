#!/usr/bin/env python3
"""Lock tokens into vault."""
import sys
from solana.rpc.api import Client
from solders.keypair import Keypair  
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM
from solders.system_program import create_account, assign, AssignParams
from spl.token.constants import TOKEN_2022_PROGRAM_ID
from spl.token.instructions import transfer_checked, TransferCheckedParams, create_associated_token_account, CreateAssociatedTokenAccountParams
import struct

PROG = "EiNHPv89CvbRLF5ioYAHqGNvrPPXZUEiLkGUBVfbJxto"

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 lock_tokens.py <vault> <source_token_account> <amount>")
        sys.exit(1)
    
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROG)
    system_id = P.from_string("11111111111111111111111111111111")
    token_prog = P.from_string("TokenkegQfeZyiNwAJpNbcdiL1CgYNJaFBY4FN4J3yNs")
    
    vault = P.from_string(sys.argv[1])
    source = P.from_string(sys.argv[2])
    amount = int(sys.argv[3])
    
    lock_ix = Instruction(
        program_id=prog,
        accounts=[
            AM(pubkey=vault, is_signer=False, is_writable=True),
            AM(pubkey=source, is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=False),
            AM(pubkey=token_prog, is_signer=False, is_writable=False),
        ],
        data=bytes([1]) + struct.pack("<Q", amount),
    )
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([lock_ix], payer, blockhash)
    txn = Transaction([kp], msg, blockhash)
    result = client.send_transaction(txn)
    print(f"Locked: {result.value}")

if __name__ == "__main__":
    main()