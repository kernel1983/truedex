import random
import string

latest_block_number = 0
states = [{}]  # one state per block
blocks = {}  # block_number -> [tx_hashes]
block_hashes = {}  # block_number -> block_hash
transactions = {}  # tx_hash -> tx
events = {}  # block_number -> [{event, args}, ...]
nonces = {}  # addr -> nonce

sender = None


def _gen_block_hash():
    return ''.join(random.choices(string.hexdigits.lower(), k=64))


def put(_owner, _asset, _var, _value, _key = None):
    global sender

    assert type(_var) is str
    if _key is not None:
        assert type(_key) is str
        var = '%s:%s' % (_var, _key)
    else:
        var = _var

    asset_name = _asset
    addr = _owner
    k = '%s-%s' % (asset_name, var)
    state = states[-1]
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
    for state in reversed(states):
        if k in state:
            addr, v = state[k]
            return v, addr

    return value, None

def event(_event, _args, _block=None):
    global states, latest_block_number
    block = _block if _block is not None else latest_block_number
    if block not in events:
        events[block] = []
    events[block].append({'event': _event, 'args': _args})

def handle_lookup(_addr):
    return _addr

def nextblock():
    global states, latest_block_number
    global blocks, block_hashes

    block_hash = _gen_block_hash()
    blocks[latest_block_number] = []
    block_hashes[latest_block_number] = block_hash

    latest_block_number += 1
    states.append({})

