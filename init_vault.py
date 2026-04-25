#!/usr/bin/env python3
"""Initialize vault."""
import sys
from solana.rpc.api import Client
from solders.keypair import Keypair  
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM
from solders.system_program import create_account, assign, AssignParams

PROG = "8ZTKLtRRoji4AwAmYwguNkC1VgJszD1rdASZhxSbRLXA"

def main():
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROG)
    system_id = P.from_string("11111111111111111111111111111111")
    
    # Calculate PDA
    vault_pda, _ = P.find_program_address([b"vault"], prog)
    print(f"Vault PDA: {vault_pda}")
    
    init_ix = Instruction(
        program_id=prog,
        accounts=[
            AM(pubkey=vault_pda, is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=True),
            AM(pubkey=payer, is_signer=False, is_writable=False), # Operator
            AM(pubkey=system_id, is_signer=False, is_writable=False),
        ],
        data=bytes([0]),
    )
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([init_ix], payer, blockhash)
    txn = Transaction([kp], msg, blockhash)
    result = client.send_transaction(txn)
    print(f"Initialized vault (PDA): {vault_pda}")
    print(f"Signature: {result.value}")

if __name__ == "__main__":
    main()