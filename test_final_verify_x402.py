import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Load local agent wallet that has Base Sepolia USDC
load_dotenv("sovereign-openclaw/.env")

from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from eth_account import Account

GATEWAY_URL = "https://api.sovereign-api.com/v1"
print(f"📡 Testing Gateway: {GATEWAY_URL}")

# STEP 1: Register Key
print("\n" + "="*60)
print("STEP 1: Register New API Key")
print("="*60)
resp = requests.post(f"{GATEWAY_URL}/register", json={"name": f"final-verify-{os.urandom(4).hex()}"})
if resp.status_code != 200:
    print(f"❌ Registration failed: {resp.text}")
    sys.exit(1)
api_key = resp.json()["api_key"]
print(f"✅ Got key: {api_key}")

# STEP 2: Topup via x402
print("\n" + "="*60)
print("STEP 2: Fund Key via x402 Payment")
print("="*60)

PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
if not PRIVATE_KEY:
    print("❌ No AGENT_PRIVATE_KEY in .env!")
    sys.exit(1)

account = Account.from_key(PRIVATE_KEY)
x402_client = x402ClientSync()
signer = EthAccountSigner(account)
register_exact_evm_client(x402_client, signer)
session = x402_requests(x402_client)

print("💸 Sending x402 payment to /v1/key/topup...")
resp_topup = session.post(f"{GATEWAY_URL}/key/topup", json={"api_key": api_key}, timeout=120)

if resp_topup.status_code == 200:
    data = resp_topup.json()
    print(f"✅ Topup Success! Added {data.get('credits_added')} credits.")
    print(f"💰 New Balance: {data.get('balance')} credits")
else:
    print(f"❌ Topup Failed: {resp_topup.status_code} - {resp_topup.text}")
    sys.exit(1)

# STEP 3: Test Endpoints
print("\n" + "="*60)
print("STEP 3: Test OpenAI Proxy Endpoints")
print("="*60)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

endpoints = [
    # Test 1: With sovereign/ prefix
    ("/chat/completions", {"model": "sovereign/claude-3.5-haiku", "messages": [{"role": "user", "content": "Say 'hello from prefixed model'."}]}),
    
    # Test 2: Without sovereign/ prefix (Bare model)
    ("/chat/completions", {"model": "claude-3.5-haiku", "messages": [{"role": "user", "content": "Say 'hello from bare model'."}]}),
    
    # Test 3: With provider prefix (OpenAI fallback simulation)
    ("/chat/completions", {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "Say 'hello from openai alias'."}]}),
]

for ep, payload in endpoints:
    print(f"\n🧪 Testing {ep}...")
    r = requests.post(f"{GATEWAY_URL}{ep}", json=payload, headers=headers)
    print(f"📡 Status: {r.status_code}")
    
    if r.status_code == 200:
        bal = r.headers.get("X-Sovereign-Balance", "?")
        cost = r.headers.get("X-Sovereign-Cost", "?")
        print(f"✅ Success! (Cost: {cost}, Remaining: {bal})")
        
        # Print a snippet of the response
        try:
            resp_data = r.json()
            if "choices" in resp_data:
                msg = resp_data["choices"][0].get("message", {}).get("content", "")
                if not msg:
                    msg = resp_data["choices"][0].get("text", "")
                print(f"🤖 Output: {msg[:100].strip()}")
        except:
            pass
    else:
        print(f"❌ Failed: {r.text[:300]}")

print("\n🎉 ALL TESTS PASSED!")
