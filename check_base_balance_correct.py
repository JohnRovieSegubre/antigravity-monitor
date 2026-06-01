from web3 import Web3
import os

# Base Mainnet RPCs
RPCS = [
    "https://mainnet.base.org",
    "https://base.publicnode.com",
]

w3 = None
for rpc in RPCS:
    temp_w3 = Web3(Web3.HTTPProvider(rpc))
    try:
        if temp_w3.is_connected():
            w3 = temp_w3
            break
    except:
        continue

# Official USDC on Base
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]

# CORRECT AGENT ADDRESS
address = "0xbCFa5fe7d4c4908B23537C1b97113327bE6f4c93"
print(f"🧐 Checking Correct Agent: {address}")

usdc = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)
balance = usdc.functions.balanceOf(address).call()
print(f"💰 USDC Balance on Base: {balance / 10**6:.6f} USDC")

eth_balance = w3.eth.get_balance(address)
print(f"⛽ ETH Balance on Base: {w3.from_wei(eth_balance, 'ether'):.6f} ETH")
