import random
import string

latest_block_number = 0
states = {}  # block_number -> {k: (addr, value)}  # one state per block
current_block_number = None  # current block being processed
blocks = {}  # block_number -> [tx_hashes]
block_hashes = {}  # block_number -> block_hash
block_times = {}  # block_number -> unix timestamp (seconds)
transactions = {}  # tx_hash -> tx
events = {}  # block_number -> [{event, args}, ...]
nonces = {}  # addr -> nonce

sender = None


def _gen_block_hash():
    return ''.join(random.choices(string.hexdigits.lower(), k=64))


def put(_owner, _asset, _var, _value, _key = None):
    global sender, current_block_number

    assert type(_var) is str
    if _key is not None:
        assert type(_key) is str
        var = '%s:%s' % (_var, _key)
    else:
        var = _var

    asset_name = _asset
    addr = _owner
    k = '%s-%s' % (asset_name, var)
    block_num = current_block_number if current_block_number is not None else latest_block_number
    if block_num not in states:
        states[block_num] = {}
    state = states[block_num]
    state[k] = addr, _value

def get(_asset, _var, _default = None, _key = None):
    global sender
    global states

    asset_name = _asset
    value = _default
    assert type(_var) is str
    if _key is not None:
        assert type(_key) is str
        var = '%s:%s' % (_var, _key)
    else:
        var = _var

    k = '%s-%s' % (asset_name, var)
    # 按 block_number 从大到小遍历（最新的block优先）
    for block_num in sorted(states.keys(), reverse=True):
        state = states[block_num]
        if k in state:
            addr, v = state[k]
            return v, addr

    return value, None

def event(_event, _args, _block=None):
    global states, latest_block_number, current_block_number
    block = _block if _block is not None else (current_block_number if current_block_number is not None else latest_block_number)
    if block not in events:
        events[block] = []
    events[block].append({'event': _event, 'args': _args})

def handle_lookup(_addr):
    return _addr

def nextblock(slot=None, timestamp=None):
    global states, latest_block_number, current_block_number
    global blocks, block_hashes, block_times

    # 如果指定了slot且已存在，不创建新block（同一个slot的多笔交易）
    if slot is not None and slot in blocks:
        # 更新时间戳（如果提供了新的）
        if timestamp is not None:
            block_times[slot] = timestamp
        current_block_number = slot
        return slot

    block_hash = _gen_block_hash()
    block_number = slot if slot is not None else latest_block_number

    blocks[block_number] = []
    block_hashes[block_number] = block_hash

    if timestamp is None:
        import time
        timestamp = int(time.time())
    block_times[block_number] = timestamp

    if slot is None:
        latest_block_number += 1
    else:
        latest_block_number = max(latest_block_number, slot + 1)

    states[block_number] = {}
    current_block_number = block_number
    return block_number

