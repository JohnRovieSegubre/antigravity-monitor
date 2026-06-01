"""
Test: Burst Session Mode — Final (Both Fixes Deployed)
=======================================================
Fix 1: Gateway now returns x402 format (not L402) for session deposits
Fix 2: topup_balance uses MINT.create_session() for SQLite persistence

Step 1: x402 auto-pay WITH X-Sovereign-Session-Deposit header
Step 2: Extract session Macaroon from response header
Step 3: Reuse Macaroon for a second call (no wallet signing)
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")

GATEWAY_URL = os.getenv("GATEWAY_URL", "https://api.sovereign-api.com/v1")
PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

if not PRIVATE_KEY:
    print("❌ No AGENT_PRIVATE_KEY in .env")
    sys.exit(1)

from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from eth_account import Account

account = Account.from_key(PRIVATE_KEY)
print(f"📡 Gateway: {GATEWAY_URL}")
print(f"🔑 Wallet: {account.address}")

# Create x402 session
x402_client = x402ClientSync()
signer = EthAccountSigner(account)
register_exact_evm_client(x402_client, signer)
x402_session = x402_requests(x402_client)

url = f"{GATEWAY_URL}/chat/completions"

# ============================================================
# STEP 1: x402 auto-pay + Session Deposit header
# ============================================================
print("\n" + "="*60)
print("STEP 1: x402 Payment + Session Deposit")
print("="*60)

payload = {
    "model": "sovereign/deepseek-r1",
    "messages": [{"role": "user", "content": "Say 'Burst Active' in one sentence."}]
}

# Set the session deposit header on the x402 session
x402_session.headers["X-Sovereign-Session-Deposit"] = "20000"
x402_session.headers["X-Sovereign-Session-TTL"] = "900"

print(f"   Deposit: 20000 sats, TTL: 900s")
print(f"🔄 Sending via x402 with session deposit...")

try:
    resp = x402_session.post(url, json=payload, timeout=120)
    
    print(f"\n📡 Status: {resp.status_code}")
    
    # Look for the minted Macaroon
    macaroon_token = None
    for key in ["X-Sovereign-Macaroon", "X-Sovereign-Token", "X-Sovereign-Balance-Token"]:
        val = resp.headers.get(key)
        if val:
            macaroon_token = val
            print(f"   ✅ {key}: {val[:50]}...")
            break
    
    # Print all sovereign headers
    for k, v in resp.headers.items():
        if "sovereign" in k.lower() or "payment" in k.lower():
            print(f"   {k}: {v[:80]}")
    
    if resp.status_code == 200:
        data = resp.json()
        if "choices" in data:
            print(f"\n🤖 Model: {data['choices'][0]['message']['content'][:150]}")
    else:
        print(f"\n📡 Body: {resp.text[:300]}")
        
except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    macaroon_token = None

# ============================================================
# STEP 2: Reuse Macaroon (no wallet, no signing)
# ============================================================
if macaroon_token:
    print("\n" + "="*60)
    print("STEP 2: Using Macaroon (NO wallet signing)")
    print("="*60)
    
    payload2 = {
        "model": "sovereign/deepseek-r1",
        "messages": [{"role": "user", "content": "Say 'Session reuse works!' in one sentence."}]
    }
    
    print(f"🔄 Sending with Bearer token only...")
    resp2 = requests.post(url, json=payload2, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {macaroon_token}"
    }, timeout=120)
    
    print(f"📡 Status: {resp2.status_code}")
    for k, v in resp2.headers.items():
        if "sovereign" in k.lower():
            print(f"   {k}: {v[:80]}")
    
    if resp2.status_code == 200:
        data2 = resp2.json()
        if "choices" in data2:
            print(f"🤖 Model: {data2['choices'][0]['message']['content'][:200]}")
        print("\n✅✅✅ BURST SESSION MODE WORKS! Macaroon reuse confirmed!")
    else:
        print(f"📡 Body: {resp2.text[:300]}")
        print(f"\n❌ Macaroon reuse failed: {resp2.status_code}")
else:
    print("\n⚠️ No Macaroon received. Burst Session not available.")
    print("   The gateway paid via x402 but didn't mint a session token.")
    print("   Check if X-Sovereign-Session-Deposit header was processed.")
