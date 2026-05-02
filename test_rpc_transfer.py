import sys
import time
from setting import accounts, RPC_URL
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

# 默认资金来源（需要有 SOL）
DEFAULT_KEYPAIR_PATH = "/home/debian/.config/solana/id.json"

def transfer_sol(client, from_kp, to_pubkey, amount_sol):
    """转账 SOL（1 SOL = 10^9 lamports）"""
    from solders.system_program import transfer, TransferParams
    from solders.message import Message
    from solders.transaction import Transaction
    
    lamports = int(amount_sol * 10**9)
    ix = transfer(TransferParams(
        from_pubkey=from_kp.pubkey(),
        to_pubkey=to_pubkey,
        lamports=lamports
    ))
    
    # 正确构造交易：先创建 Message，再创建 Transaction
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([ix], from_kp.pubkey(), blockhash)
    txn = Transaction([from_kp], msg, blockhash)
    result = client.send_transaction(txn)
    return str(result.value)

def transfer_tokens(client, from_kp, to_pubkey, token, amount, decimals):
    """转账代币（USDC/BTC）"""
    from test_rpc_init import transaction
    
    call = {
        "p": "zen",
        "f": "token_transfer",
        "a": [token, str(to_pubkey), int(amount * 10**decimals)]
    }
    print(f"转账 {amount} {token} 给 {to_pubkey}")
    call_json = json.dumps(call)
    tx_hash = transaction(call_json, from_kp)
    return tx_hash

if __name__ == '__main__':
    import json
    from test_rpc_init import transaction
    
    client = Client(RPC_URL)
    
    # 加载默认资金来源
    funder = Keypair.from_json(open(DEFAULT_KEYPAIR_PATH).read())
    print(f"资金来源: {funder.pubkey()}")
    
    # 检查并给每个测试账户转 SOL（gas）
    print("\n=== 给测试账户转 SOL (gas) ===")
    for i, kp in enumerate(accounts):
        pubkey = kp.pubkey()
        
        # 检查余额
        balance = client.get_balance(pubkey).value
        balance_sol = balance / 10**9
        print(f"账户{i} ({pubkey}) 余额: {balance_sol:.4f} SOL")
        
        if balance_sol < 0.1:  # 少于0.1 SOL就转
            print(f"  转账 1.0 SOL 作为 gas...")
            try:
                tx_hash = transfer_sol(client, funder, pubkey, 1.0)
                print(f"  交易: {tx_hash}")
                time.sleep(2)
            except Exception as e:
                print(f"  转账失败: {e}")
    
    # 给测试账户转 USDC 和 BTC
    print("\n=== 转账代币 ===")
    for i, kp in enumerate(accounts[1:], 1):  # 跳过account0（默认是资金来源）
        pubkey = str(kp.pubkey())
        
        # 转 USDC
        call = json.dumps({
            "p": "zen",
            "f": "token_transfer",
            "a": ["USDC", pubkey, 15000000000000]  # 15000 USDC
        })
        print(f"账户{i} 转 USDC...")
        tx_hash = transaction(call, funder)
        print(f"  交易: {tx_hash}")
        
        # 转 BTC
        call = json.dumps({
            "p": "zen",
            "f": "token_transfer",
            "a": ["BTC", pubkey, 100000000000000000000]  # 100 BTC
        })
        print(f"账户{i} 转 BTC...")
        tx_hash = transaction(call, funder)
        print(f"  交易: {tx_hash}")
        
        time.sleep(1)

    to = 'im3ZVx56GK7JQxi3UVBC3N2bQF3QDcAwfrvcvREZrgm'
    pubkey = Pubkey.from_string(to)
    tx_hash = transfer_sol(client, funder, pubkey, 1.0)

    call = '{"p": "zen", "f": "token_transfer", "a": ["USDC", "%s", 15000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    call = '{"p": "zen", "f": "token_transfer", "a": ["BTC", "%s", 100000000000000000000]}' % to
    print(call)
    tx_hash = transaction(call)
    print(tx_hash)

    print("\n✅ 完成！")
