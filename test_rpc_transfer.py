import sys
import hashlib
import json
import setting
from test_rpc_init import transaction
from setting import accounts

if __name__ == '__main__':
    for i in range(1, 10):
        to = accounts[i].pubkey()
        call = '{"p": "zen", "f": "token_transfer", "a": ["USDC", "%s", 15000000000000]}' % to
        print(call)
        tx_hash = transaction(call)
        print(tx_hash)

        call = '{"p": "zen", "f": "token_transfer", "a": ["BTC", "%s", 100000000000000000000]}' % to
        print(call)
        tx_hash = transaction(call)
        print(tx_hash)


    to = 'im3ZVx56GK7JQxi3UVBC3N2bQF3QDcAwfrvcvREZrgm'
    call = '{"p": "zen", "f": "token_transfer", "a": ["USDC", "%s", 15000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_transfer", "a": ["BTC", "%s", 100000000000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)


    to = '9XUk72GUg21FDxZBrmqxhumpBEynCAekRHoFmnRP5CqJ'
    call = '{"p": "zen", "f": "token_transfer", "a": ["USDC", "%s", 15000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_transfer", "a": ["BTC", "%s", 100000000000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

