import sys
import hashlib
import json

from test_rpc_init import transaction

if __name__ == '__main__':
    call = {"p": "zen", "f": "trade_market_order", "a": ["BTC", int(float(sys.argv[1])*10**18), "USDC", int(float(sys.argv[2])*10**6)]}
    print(call)
    call_json = json.dumps(call)
    tx_hash = transaction(call_json)
    print(tx_hash)
