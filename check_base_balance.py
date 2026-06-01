from web3 import Web3
import os

# Base Mainnet RPCs
RPCS = [
    "https://mainnet.base.org",
    "https://base.publicnode.com",
    "https://developer-access-mainnet.base.org"
]

w3 = None
for rpc in RPCS:
    temp_w3 = Web3(Web3.HTTPProvider(rpc))
    try:
        if temp_w3.is_connected():
            w3 = temp_w3
            print(f"✅ Connected to: {rpc}")
            break
    except:
        continue

if not w3:
    print("❌ All Base RPCs failed.")
    exit(1)

# Official USDC on Base
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]

address = "0xC8Dc2795352cdedEF3a11f1fC9E360D85C5aAC4d"
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)

balance = usdc.functions.balanceOf(address).call()
print(f"💰 USDC Balance on Base: {balance / 10**6:.6f} USDC")

eth_balance = w3.eth.get_balance(address)
print(f"⛽ ETH Balance on Base: {w3.from_wei(eth_balance, 'ether'):.6f} ETH")
