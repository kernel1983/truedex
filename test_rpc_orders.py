import sys
import hashlib
import json
import random

import setting
from test_rpc_init import transaction, next_block

if __name__ == '__main__':
    accounts = setting.accounts

    print('=== Create SELL limit orders ===')
    for i in range(3):
        price = 660 + i * 10
        amount = 1 * 10**18
        quote = price * 10**6
        call = f'{{"p": "zen", "f": "trade_limit_order", "a": ["BTC", -{amount}, "USDC", {quote}]}}'
        print(f'Sell Limit {i+1}: price={price}, amount={amount // 10**18}')
        tx_hash = transaction(call)
        print(f'  tx: {tx_hash}')

    print('\n=== next block ===')
    next_block()

    print('=== Create BUY limit orders ===')
    for i in range(3):
        price = 640 - i * 10
        amount = 1 * 10**18
        quote = price * 10**6
        call = f'{{"p": "zen", "f": "trade_limit_order", "a": ["BTC", {amount}, "USDC", -{quote}]}}'
        print(f'Buy Limit {i+1}: price={price}, amount={amount // 10**18}')
        tx_hash = transaction(call)
        print(f'  tx: {tx_hash}')

    print('\n=== next block ===')
    next_block()

    print('=== Market SELL ===')
    amount = 0.1 * 10**18
    call = f'{{"p": "zen", "f": "trade_market_order", "a": ["BTC", -{amount}, "USDC", null]}}'
    print(f'Market SELL: amount={amount // 10**18}')
    tx_hash = transaction(call)
    print(f'  tx: {tx_hash}')

    print('\n=== next block ===')
    next_block()

    print('=== Market BUY ===')
    amount = 100 * 10**6
    call = f'{{"p": "zen", "f": "trade_market_order", "a": ["BTC", null, "USDC", -{amount}]}}'
    print(f'Market BUY: amount={amount // 10**18}')
    tx_hash = transaction(call)
    print(f'  tx: {tx_hash}')

    print('\n=== next block ===')
    next_block()

    print('\n=== Done ===')