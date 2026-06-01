"""
Definitive Test: x402 Guest Mode (Pure Mode)
=============================================
Following the OFFICIAL skill.md and x402 SDK docs.
No API key. No Macaroon. Just wallet.
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")

GATEWAY_URL = os.getenv("GATEWAY_URL", "https://api.sovereign-api.com/v1")
PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

if not PRIVATE_KEY:
    print("❌ No AGENT_PRIVATE_KEY in .env")
    sys.exit(1)

print(f"📡 Gateway: {GATEWAY_URL}")

# === TEST: x402 Guest Mode ===
from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from eth_account import Account

account = Account.from_key(PRIVATE_KEY)
print(f"🔑 Wallet: {account.address}")

# 1. Create x402 client
x402_client = x402ClientSync()

# 2. Register EVM signer
signer = EthAccountSigner(account)
register_exact_evm_client(x402_client, signer)

# 3. Create payment-aware session
session = x402_requests(x402_client)

# 4. Send request — NO API KEY, NO MACAROON
url = f"{GATEWAY_URL}/chat/completions"
payload = {
    "model": "sovereign/deepseek-r1",
    "messages": [{"role": "user", "content": "Say hello in one sentence. Keep it very short."}]
}

print(f"\n🔄 Sending to {payload['model']} via x402 Guest Mode...")
print(f"   Headers: Content-Type only (no API key, no token)")

try:
    resp = session.post(url, json=payload, timeout=120)
    
    print(f"\n📡 Final Status: {resp.status_code}")
    print(f"📡 Response Headers:")
    for k, v in resp.headers.items():
        print(f"   {k}: {v[:120]}")
    
    body = resp.text
    print(f"\n📡 Response Body ({len(body)} chars):")
    print(body[:1000])
    
    if resp.status_code == 200:
        print("\n✅✅✅ GUEST MODE WORKS! Wallet-only compute confirmed.")
        data = resp.json()
        if "choices" in data:
            print(f"🤖 Model said: {data['choices'][0]['message']['content'][:200]}")
    elif resp.status_code == 401:
        print(f"\n❌ 401 Unauthorized — Gateway rejected AFTER payment.")
        print("   This means Guest Mode payment worked but upstream failed.")
    elif resp.status_code == 402:
        print(f"\n❌ 402 — Payment was NOT auto-handled by x402 SDK.")
    else:
        print(f"\n⚠️ Unexpected status: {resp.status_code}")

except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
