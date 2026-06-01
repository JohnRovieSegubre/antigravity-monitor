import requests
from eth_account import Account

# Wallet Configuration
priv_key = "0xcd4a1e47dcac125cbfd4b66de62c8860f4528749a694d5c064824886d18156fb"
account = Account.from_key(priv_key)
address = account.address
print(f"Wallet Address: {address}")

# RPC Configuration
RPC_URL = "https://sepolia.base.org"

def get_balance(address):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1
    }
    response = requests.post(RPC_URL, json=payload)
    result = response.json().get("result")
    if result:
        balance_wei = int(result, 16)
        return balance_wei / 1e18
    return 0

def get_token_balance(address, token_address):
    # balanceOf selector: 0x70a08231
    data = "0x70a08231" + address[2:].lower().zfill(64)
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": token_address, "data": data},
            "latest"
        ],
        "id": 1
    }
    response = requests.post(RPC_URL, json=payload)
    result = response.json().get("result")
    if result and result != "0x":
        return int(result, 16)
    return 0

# Base Sepolia USDC address
USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

eth_balance = get_balance(address)
usdc_balance_raw = get_token_balance(address, USDC_ADDRESS)
usdc_balance = usdc_balance_raw / 1e6

print(f"ETH Balance: {eth_balance} ETH")
print(f"USDC Balance: {usdc_balance} USDC")
