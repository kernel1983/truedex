import hashlib
from solders.keypair import Keypair

USE_DEVNET = True  # Set to True for devnet, False for local test validator

accounts = []
for i in range(10):
    seed = hashlib.sha256(('brownie%s' % i).encode('utf8')).digest()
    account = Keypair.from_seed(seed)
    accounts.append(account)

# Local test validator
PROGRAM_ID = "2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih"
RPC_URL = "http://localhost:8899"
WS_URL = "ws://localhost:8900"

# Devnet (used when USE_DEVNET = True)
DEVNET_RPC_URL = "https://api.devnet.solana.com"
DEVNET_WS_URL = "wss://api.devnet.solana.com"
DEVNET_PROGRAM_ID = "2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih"

