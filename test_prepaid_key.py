"""
Test: Seamless Prepaid API Key System (End-to-End)
===================================================
Step 1: Register a new API key
Step 2: Check balance (should be 0)
Step 3: Try to use it for chat (should get 403, not 402)
Step 4: Guest mode regression (wallet-only still works)
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")

GATEWAY_URL = os.getenv("GATEWAY_URL", "https://api.sovereign-api.com/v1")
print(f"📡 Gateway: {GATEWAY_URL}")

# ============================================================
# STEP 1: Register
# ============================================================
print("\n" + "="*60)
print("STEP 1: Register New API Key")
print("="*60)

resp = requests.post(f"{GATEWAY_URL}/register", json={"name": f"prepaid-test-{os.urandom(4).hex()}"}, timeout=10)
print(f"📡 Status: {resp.status_code}")
print(f"📡 Body: {resp.text[:300]}")

api_key = None
if resp.status_code == 200:
    data = resp.json()
    api_key = data.get("api_key")
    print(f"✅ Got key: {api_key}")
else:
    print("❌ Registration failed")
    sys.exit(1)

# ============================================================
# STEP 2: Check Balance (should be 0)
# ============================================================
print("\n" + "="*60)
print("STEP 2: Check Key Balance")
print("="*60)

resp2 = requests.get(f"{GATEWAY_URL}/key/balance", headers={
    "Authorization": f"Bearer {api_key}"
}, timeout=10)
print(f"📡 Status: {resp2.status_code}")
print(f"📡 Body: {resp2.text[:300]}")

if resp2.status_code == 200:
    bal = resp2.json()
    print(f"   Balance: {bal.get('balance', '?')} credits")
    print(f"   Funded: {bal.get('funded', '?')}")

# ============================================================
# STEP 3: Use Key for Chat (should get 403, NOT 402)
# ============================================================
print("\n" + "="*60)
print("STEP 3: Try Chat with Unfunded Key (expect 403)")
print("="*60)

resp3 = requests.post(f"{GATEWAY_URL}/chat/completions", json={
    "model": "sovereign/deepseek-r1",
    "messages": [{"role": "user", "content": "Say hi"}]
}, headers={
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}, timeout=15)

print(f"📡 Status: {resp3.status_code}")
print(f"📡 Body: {resp3.text[:300]}")

if resp3.status_code == 403:
    print("✅ Correctly returned 403 (not 402). Won't trigger x402 auto-pay!")
elif resp3.status_code == 402:
    print("❌ Got 402 — this would trigger x402 auto-pay. BUG!")
else:
    print(f"⚠️ Unexpected: {resp3.status_code}")

# ============================================================
# STEP 4: Guest Mode Regression
# ============================================================
print("\n" + "="*60)
print("STEP 4: Guest Mode Regression (x402 wallet-only)")
print("="*60)

from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from eth_account import Account

PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
if PRIVATE_KEY:
    account = Account.from_key(PRIVATE_KEY)
    x402_client = x402ClientSync()
    signer = EthAccountSigner(account)
    register_exact_evm_client(x402_client, signer)
    session = x402_requests(x402_client)

    resp4 = session.post(f"{GATEWAY_URL}/chat/completions", json={
        "model": "sovereign/deepseek-r1",
        "messages": [{"role": "user", "content": "Say 'guest mode ok' in one sentence"}]
    }, timeout=120)

    print(f"📡 Status: {resp4.status_code}")
    if resp4.status_code == 200:
        data4 = resp4.json()
        if "choices" in data4:
            print(f"🤖 Model: {data4['choices'][0]['message']['content'][:150]}")
        print("✅ Guest Mode still works!")
    else:
        print(f"📡 Body: {resp4.text[:300]}")
        print(f"⚠️ Guest Mode returned {resp4.status_code}")
else:
    print("⚠️ No AGENT_PRIVATE_KEY — skipping Guest Mode test")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"API Key: {api_key}")
print("Next: Fund this key via /v1/key/topup (x402 payment)")
print("Then: Use it like OpenAI: Authorization: Bearer sk-sov-xxx")
