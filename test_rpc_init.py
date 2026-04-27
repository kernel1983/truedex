import time

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey as P
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta as AM

from setting import PROGRAM_ID

def transaction(call):
    client = Client("http://localhost:8899")
    kp = Keypair.from_json(open("/home/debian/.config/solana/id.json").read())
    payer = kp.pubkey()
    prog = P.from_string(PROGRAM_ID)
    
    print(f"{payer} executing call")
    data = call.encode('utf8')
    
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
    return str(result.value)

def next_block():
    time.sleep(1)
    return {"result": "slept 1s for solana block propagation"}


if __name__ == '__main__':
    call = '{"p": "zen", "f": "asset_create", "a": ["USDC"]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_create", "a": ["USDC", "Mock USDC", 6]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)


    call = '{"p": "zen", "f": "asset_create", "a": ["BTC"]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_create", "a": ["BTC", "Mock BTC", 18]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    print('=== Call next block ===')
    result = next_block()
    print('next block result:', result)
