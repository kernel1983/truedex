import sys
import hashlib
import json


import setting

from test_rpc_init import *

if __name__ == '__main__':
    call = '{"p": "zen", "f": "token_mint_once", "a": ["USDC", 8595000000000000]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_mint_once", "a": ["BTC", 2100000000000000000000]}'
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)
