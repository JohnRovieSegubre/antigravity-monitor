import time
import requests
from web3 import Web3
from eth_account import Account

# --- CONFIGURATION ---
RPC_URL = "https://sepolia.base.org"
USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
PAY_TO_ADDRESS = "0xC8Dc2795352cdedEF3a11f1fC9E360D85C5aAC4d"
PRIV_KEY = "0xcd4a1e47dcac125cbfd4b66de62c8860f4528749a694d5c064824886d18156fb"
API_KEY = "sk-sov-97cd2d376195be7cec0b01da621030d8"
AMOUNT_USDC = 1.0  # $1.00

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIV_KEY)
address = account.address

print(f"Using address: {address}")

# 1. Prepare USDC Transfer
usdc_abi = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=usdc_abi)
amount_raw = int(AMOUNT_USDC * 1e6)  # 6 decimals for USDC

nonce = w3.eth.get_transaction_count(address)
gas_price = w3.eth.gas_price

# Use a slightly higher gas price to ensure confirmation
tx = usdc_contract.functions.transfer(PAY_TO_ADDRESS, amount_raw).build_transaction({
    'from': address,
    'nonce': nonce,
    'gas': 100000,
    'gasPrice': int(gas_price * 1.2),
    'chainId': 84532
})

# 2. Sign and Send
signed_tx = w3.eth.account.sign_transaction(tx, PRIV_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
tx_hash_hex = tx_hash.hex()

print(f"Transaction submitted: {tx_hash_hex}")
print("Waiting for confirmation...")

# 3. Wait for Receipt
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
if receipt.status == 1:
    print("Transaction confirmed!")
    
    # 4. Notify Gateway
    url = "https://api.sovereign-api.com/v1/key/topup"
    headers = {
        "Authorization": f'L402 macaroon="", receipt="{tx_hash_hex}"'
    }
    body = {"api_key": API_KEY}
    
    print(f"Calling gateway: {url}")
    response = requests.post(url, json=body, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print("Transaction FAILED on-chain.")
