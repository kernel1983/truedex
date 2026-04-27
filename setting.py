import hashlib
from solders.keypair import Keypair

accounts = []
for i in range(10):
    seed = hashlib.sha256(('brownie%s' % i).encode('utf8')).digest()
    account = Keypair.from_seed(seed)
    accounts.append(account)

PROGRAM_ID = "2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih"

