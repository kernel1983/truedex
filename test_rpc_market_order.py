import sys
import json
import time
import requests

from test_rpc_init import transaction

from setting import accounts

SERVER_URL = "http://localhost:3000"

DEFAULT_ACCOUNT = 0

def get_balance(pubkey, token):
    """查询账户代币余额"""
    prefix = f"{token}-balance:{pubkey}"
    try:
        resp = requests.get(f"{SERVER_URL}/api/get_latest_state?prefix={prefix}")
        data = resp.json()
        decimals = {"BTC": 18, "USDC": 6}
        dec = decimals.get(token, 6)
        raw = data.get("result")
        if raw is None:
            return 0.0
        return raw / (10 ** dec)
    except Exception as e:
        print(f"查询 {token} 余额失败: {e}")
        return 0.0

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("用法: python test_rpc_market_order.py <account_num> <base_amount> <quote_amount>")
        print("示例（买入BTC，使用账户0）: python test_rpc_market_order.py 0 0.1 null")
        print("示例（卖出BTC，使用账户1）: python test_rpc_market_order.py 1 -0.1 null")
        print(f"\n可用账户: 0-{len(accounts)-1}")
        sys.exit(1)

    account_num = int(sys.argv[1])
    if account_num >= len(accounts):
        print(f"错误: 账户 {account_num} 不存在 (共 {len(accounts)} 个账户)")
        sys.exit(1)

    base_amount = int(float(sys.argv[2]) * 10**18)
    # quote_amount 可能是 null 或数字
    if sys.argv[3].lower() == 'null':
        quote_amount = None
    else:
        quote_amount = int(float(sys.argv[3]) * 10**6)

    kp = accounts[account_num]
    pubkey = str(kp.pubkey())

    # 查询交易前余额
    print(f"\n=== 交易前余额 (账户{account_num}) ===")
    btc_before = get_balance(pubkey, "BTC")
    usdc_before = get_balance(pubkey, "USDC")
    print(f"BTC: {btc_before:.6f}")
    print(f"USDC: {usdc_before:.6f}")

    # 构造交易
    call = {
        "p": "zen",
        "f": "trade_market_order",
        "a": ["BTC", base_amount if base_amount else None, "USDC", quote_amount if quote_amount else None]
    }
    print(f"\n=== 发送交易 ===")
    print(f"Call: {call}")
    call_json = json.dumps(call)

    # 发送交易
    tx_hash = transaction(call_json, kp)
    print(f"交易哈希: {tx_hash}")

    # 等待交易处理
    time.sleep(3)

    # 查询交易后余额
    print(f"\n=== 交易后余额 ===")
    btc_after = get_balance(pubkey, "BTC")
    usdc_after = get_balance(pubkey, "USDC")
    print(f"BTC: {btc_after:.6f} (变化: {btc_after - btc_before:+.6f})")
    print(f"USDC: {usdc_after:.6f} (变化: {usdc_after - usdc_before:+.6f})")
