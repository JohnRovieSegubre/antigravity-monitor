"""
Test 1: x402 Guest Mode (Pure Mode)
====================================
According to skill.md, this should work with JUST a wallet.
No API keys, no tokens, no accounts.

Uses the x402 Python SDK to auto-sign payments.
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
print(f"🔑 Wallet: {PRIVATE_KEY[:10]}...")

# --- Method 1: Using x402 Python SDK ---
try:
    from x402 import x402ClientSync
    from x402.http.clients import x402_requests
    from x402.mechanisms.evm import EthAccountSigner
    from x402.mechanisms.evm.exact.register import register_exact_evm_client
    from eth_account import Account
    
    print("\n=== TEST 1: x402 Guest Mode (Pure Mode) ===")
    print("No API Key. No Macaroon. Just wallet.")
    
    account = Account.from_key(PRIVATE_KEY)
    print(f"   Address: {account.address}")
    
    # Create signer
    signer = EthAccountSigner(account)
    
    # Create x402-aware session 
    session = x402_requests.x402Session(signer)
    
    # Send request with NO API key, NO Authorization header
    url = f"{GATEWAY_URL}/chat/completions"
    payload = {
        "model": "sovereign/deepseek-r1",
        "messages": [{"role": "user", "content": "Say hello in one sentence."}]
    }
    
    print(f"🔄 Sending to {payload['model']}...")
    resp = session.post(url, json=payload, timeout=120)
    
    print(f"📡 Status: {resp.status_code}")
    print(f"📡 Headers: {dict(resp.headers)}")
    print(f"📡 Body: {resp.text[:500]}")
    
    if resp.status_code == 200:
        print("\n✅ GUEST MODE WORKS! No API key needed.")
    else:
        print(f"\n❌ GUEST MODE FAILED: {resp.status_code}")
        
except ImportError as e:
    print(f"❌ x402 SDK not installed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)

# --- Method 2: Manual x402 (without SDK, raw headers) ---
try:
    import requests
    
    print("\n=== TEST 2: Raw 402 Challenge (No SDK) ===")
    print("Sending request with NO auth to see the 402 response format.")
    
    url = f"{GATEWAY_URL}/chat/completions"
    payload = {
        "model": "sovereign/deepseek-r1",
        "messages": [{"role": "user", "content": "Say hi."}]
    }
    
    resp = requests.post(url, json=payload, timeout=30)
    
    print(f"📡 Status: {resp.status_code}")
    print(f"📡 Headers:")
    for k, v in resp.headers.items():
        print(f"   {k}: {v[:100]}")
    print(f"📡 Body: {resp.text[:500]}")
    
    if resp.status_code == 402:
        # Check for x402 vs L402 headers
        payment_required = resp.headers.get("payment-required") or resp.headers.get("PAYMENT-REQUIRED")
        www_auth = resp.headers.get("WWW-Authenticate", "")
        
        if payment_required:
            print("\n🔍 x402 PAYMENT-REQUIRED header found!")
            try:
                decoded = json.loads(
                    __import__('base64').b64decode(payment_required).decode()
                )
                print(f"   Decoded: {json.dumps(decoded, indent=2)}")
            except:
                print(f"   Raw: {payment_required[:200]}")
        
        if "L402" in www_auth:
            print(f"\n🔍 L402 challenge found: {www_auth[:200]}")
        
        if not payment_required and "L402" not in www_auth:
            print("\n⚠️ Neither x402 nor L402 headers found!")

except Exception as e:
    print(f"❌ Error: {e}")
