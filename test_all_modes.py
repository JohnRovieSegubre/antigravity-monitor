"""
FULL SYSTEM TEST: All Three Auth Modes
========================================
Mode A: x402 Guest Mode (wallet-only)
Mode B: Prepaid API Key (OpenAI-compatible)
Mode C: Burst Session (Macaroon)
"""
import os, sys, json, requests, time
from dotenv import load_dotenv
load_dotenv("sovereign-openclaw/.env")

GATEWAY = os.getenv("GATEWAY_URL", "https://api.sovereign-api.com/v1")
PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
MODEL = "sovereign/deepseek-r1"

from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from eth_account import Account

account = Account.from_key(PRIVATE_KEY)
x402_client = x402ClientSync()
register_exact_evm_client(x402_client, EthAccountSigner(account))
x402_session = x402_requests(x402_client)

print(f"📡 Gateway: {GATEWAY}")
print(f"🔑 Wallet: {account.address}")
results = {}

# ============================================================
# MODE A: x402 Guest Mode
# ============================================================
print("\n" + "="*60)
print("MODE A: x402 Guest Mode (wallet-only)")
print("="*60)
try:
    r = x402_session.post(f"{GATEWAY}/chat/completions", json={
        "model": MODEL, "messages": [{"role": "user", "content": "Say 'Guest OK' in 2 words max"}]
    }, timeout=120)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        msg = r.json()["choices"][0]["message"]["content"][:100]
        print(f"🤖 {msg}")
        results["guest"] = "✅ PASS"
    else:
        print(f"Body: {r.text[:200]}")
        results["guest"] = f"❌ {r.status_code}"
except Exception as e:
    print(f"❌ {e}")
    results["guest"] = f"❌ {e}"

# ============================================================
# MODE B: Prepaid API Key (Full Flow)
# ============================================================
print("\n" + "="*60)
print("MODE B: Prepaid API Key (register → topup → use → balance)")
print("="*60)

# B1: Register
print("\n--- B1: Register ---")
r = requests.post(f"{GATEWAY}/register", json={"name": f"fulltest-{os.urandom(3).hex()}"}, timeout=10)
api_key = r.json().get("api_key") if r.status_code == 200 else None
print(f"Key: {api_key}")

if api_key:
    # B2: Topup (x402 pays $1.00, credits key with 100k credits)
    print("\n--- B2: Topup via x402 ---")
    r2 = x402_session.post(f"{GATEWAY}/key/topup", json={
        "api_key": api_key, "idempotency_key": f"test_{os.urandom(8).hex()}"
    }, timeout=120)
    print(f"Status: {r2.status_code}")
    print(f"Body: {r2.text[:300]}")
    
    if r2.status_code == 200:
        topup_data = r2.json()
        print(f"Credits added: {topup_data.get('credits_added')}")
        print(f"Balance: {topup_data.get('balance')}")
        
        # B3: Use key for chat (like OpenAI!)
        print("\n--- B3: Chat with prepaid key (OpenAI-style) ---")
        r3 = requests.post(f"{GATEWAY}/chat/completions", json={
            "model": MODEL, "messages": [{"role": "user", "content": "Say 'Prepaid OK' in 2 words max"}]
        }, headers={"Authorization": f"Bearer {api_key}"}, timeout=120)
        
        print(f"Status: {r3.status_code}")
        # Check response headers
        for h in ["X-Sovereign-Balance", "X-Sovereign-Cost", "X-RateLimit-Remaining"]:
            v = r3.headers.get(h)
            if v: print(f"   {h}: {v}")
        
        if r3.status_code == 200:
            msg = r3.json()["choices"][0]["message"]["content"][:100]
            print(f"🤖 {msg}")
            
            # B4: Check balance after spend
            print("\n--- B4: Balance check ---")
            r4 = requests.get(f"{GATEWAY}/key/balance", headers={
                "Authorization": f"Bearer {api_key}"
            }, timeout=10)
            print(f"Balance: {r4.json()}")
            results["prepaid"] = "✅ PASS"
        else:
            print(f"Body: {r3.text[:200]}")
            results["prepaid"] = f"❌ Chat: {r3.status_code}"
    else:
        results["prepaid"] = f"❌ Topup: {r2.status_code}"
else:
    results["prepaid"] = "❌ Registration failed"

# ============================================================
# MODE C: Burst Session (Macaroon)
# ============================================================
print("\n" + "="*60)
print("MODE C: Burst Session (pay once, reuse token)")
print("="*60)

# C1: x402 pay + session deposit
print("\n--- C1: x402 + Session Deposit ---")
x402_session.headers["X-Sovereign-Session-Deposit"] = "20000"
x402_session.headers["X-Sovereign-Session-TTL"] = "900"
try:
    r = x402_session.post(f"{GATEWAY}/chat/completions", json={
        "model": MODEL, "messages": [{"role": "user", "content": "Say 'Burst OK' in 2 words max"}]
    }, timeout=120)
    print(f"Status: {r.status_code}")

    mac_token = r.headers.get("X-Sovereign-Macaroon")
    if mac_token:
        print(f"Macaroon: {mac_token[:40]}...")
        if r.status_code == 200:
            msg = r.json()["choices"][0]["message"]["content"][:100]
            print(f"🤖 {msg}")
        
        # C2: Reuse macaroon
        print("\n--- C2: Reuse Macaroon (no wallet) ---")
        r2 = requests.post(f"{GATEWAY}/chat/completions", json={
            "model": MODEL, "messages": [{"role": "user", "content": "Say 'Reuse OK' in 2 words max"}]
        }, headers={"Authorization": f"Bearer {mac_token}"}, timeout=120)
        
        print(f"Status: {r2.status_code}")
        bal = r2.headers.get("X-Sovereign-Macaroon-Balance")
        if bal: print(f"   Session balance: {bal}")
        
        if r2.status_code == 200:
            msg = r2.json()["choices"][0]["message"]["content"][:100]
            print(f"🤖 {msg}")
            results["burst"] = "✅ PASS"
        else:
            print(f"Body: {r2.text[:200]}")
            results["burst"] = f"❌ Reuse: {r2.status_code}"
    else:
        results["burst"] = f"❌ No macaroon returned"
except Exception as e:
    print(f"❌ {e}")
    results["burst"] = f"❌ {e}"
finally:
    del x402_session.headers["X-Sovereign-Session-Deposit"]
    del x402_session.headers["X-Sovereign-Session-TTL"]

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)
for mode, result in results.items():
    print(f"   {mode:12s}: {result}")
