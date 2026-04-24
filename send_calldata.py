#!/usr/bin/env python3
"""Initialize vault and test all instructions."""
from solana.rpc.api import Client
from solders.keypair import Keypair  
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM
from solders.system_program import create_account, assign, AssignParams

PROG = "Eicr4kGcfcP1dRcge9KMnjzcn2BNm528hbYms7qBkcEe"

def create_vault(client, kp, prog, payer):
    """Create and initialize vault."""
    system_id = P.from_string("11111111111111111111111111111111")
    
    vault = Keypair()
    
    create_ix = create_account({
        "from_pubkey": payer,
        "to_pubkey": vault.pubkey(),
        "lamports": 5000000,
        "space": 33,
        "owner": system_id,
        "program_id": system_id,
    })
    
    assign_ix = assign(AssignParams(pubkey=vault.pubkey(), owner=prog))
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([create_ix, assign_ix], payer, blockhash)
    txn = Transaction([kp, vault], msg, blockhash)
    client.send_transaction(txn)
    
    init_ix = Instruction(
        program_id=prog,
        accounts=[
            AM(pubkey=vault.pubkey(), is_signer=False, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=True),
            AM(pubkey=payer, is_signer=True, is_writable=False),
            AM(pubkey=system_id, is_signer=False, is_writable=False),
        ],
        data=bytes([0]),
    )
    
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([init_ix], payer, blockhash)
    txn = Transaction([kp], msg, blockhash)
    return client.send_transaction(txn)

def main():
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROG)
    
    print(f"Program: {prog}")
    print(f"Payer: {payer}")
    
    result = create_vault(client, kp, prog, payer)
    print(f"Initialized: {result.value}")

if __name__ == "__main__":
    main()