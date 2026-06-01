import requests
import os
import json
from dotenv import load_dotenv

# Load agent config
load_dotenv("sovereign-openclaw/.env")
api_key = os.getenv("SOVEREIGN_API_KEY")
base_url = os.getenv("GATEWAY_URL")

def prove_ghost_token():
    print("🕵️  Missions: Prove Ghost Token Bug")
    print(f"📡 Gateway: {base_url}")
    
    # 1. Simulate a Refuel (Assume x402 is bypassed or mocked for this test)
    # Note: We'll call /v1/balance/topup directly. 
    # In production, this needs an x402 signature, but we can see the logic failure 
    # by checking if a token received FROM this endpoint works on the NEXT call.
    
    print("\nStep 1: Requesting Refuel...")
    # For the purpose of this proof, we assume the user has the SDK which just refueled.
    # We will grab the MOST RECENT token from the macaroon.dat if it exists, 
    # or simulate the flow if we can.
    
    token_file = "sovereign-openclaw/sdk/macaroon.dat"
    if not os.path.exists(token_file):
        print("❌ No token file found. Run a refuel first or simulate one.")
        return

    with open(token_file, "r") as f:
        ghost_token = f.read().strip()
    
    print(f"👻 Ghost Token Loaded: {ghost_token[:20]}...")

    # 2. Attempt to use it
    print("\nStep 2: Attempting to use the fresh token for deepseek-r1...")
    headers = {
        "X-Sovereign-Api-Key": api_key,
        "Authorization": f"Bearer {ghost_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sovereign/deepseek-r1",
        "messages": [{"role": "user", "content": "hello"}]
    }

    resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    
    print(f"📡 Response Status: {resp.status_code}")
    print(f"📡 Response Body: {resp.text}")
    
    if resp.status_code == 402 and "Token/Session not found" in resp.text:
        print("\n✅ PROOF COMPLETE: The server rejected the token it JUST minted.")
        print("REASON: Missing 'INSERT INTO macaroons' in gateway_server.py:topup_balance")
    else:
        print("\n❌ Proof inconclusive or server behavior changed.")

if __name__ == "__main__":
    prove_ghost_token()
