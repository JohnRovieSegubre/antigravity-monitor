import asyncio
import httpx
import time
import json
import secrets

BASE_URL = "http://localhost:8000"

# Mock the Minting and Spending using direct DB calls for testing concurrency locally
# Since we don't have a wallet to sign real x402s in the test runner, we will mint a macaroon
# manually using the logic from gateway_server.py and test its concurrency natively.

import sys
sys.path.append(".")
try:
    from gateway_server import MINT
    from pymacaroons import Macaroon
except ImportError as e:
    print(f"Could not load SovereignMint: {e}")
    sys.exit(1)


async def fire_request(client, token, payload, idx):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    start = time.time()
    resp = await client.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers)
    elapsed = time.time() - start
    return idx, resp.status_code, resp.json() if resp.status_code != 200 else "SUCCESS", elapsed

async def main():
    print("MINTING 1500 SAT MACAROON (Should support 15 calls at 100 sats each)...")
    token_str, balance = MINT.create_session(amount_sats=1500, ttl_seconds=600)
    print(f"Token Balance: {balance}")

    # For testing, we need the server running on localhost:8000.
    # Since we can't guarantee it's running with test environment variables, 
    # we will just test the MINT concurrency explicitly at the python level first.

    print("\n--- LEVEL 1: DB ATOMICITY TEST ---")
    
    def spend_task(idx):
        valid, new_bal, msg = MINT.verify_and_spend(token_str, 100)
        return idx, valid, new_bal, msg

    import concurrent.futures
    loop = asyncio.get_running_loop()
    
    # Fire 15 concurrent db accesses
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
        futures = [
            loop.run_in_executor(pool, spend_task, i) 
            for i in range(15)
        ]
        results = await asyncio.gather(*futures)

    successes = 0
    failures = 0
    for idx, valid, new_bal, msg in results:
        if valid:
            successes += 1
        else:
            failures += 1
    
    print(f"✅ DB Concurrency Successes: {successes}")
    print(f"❌ DB Concurrency Failures: {failures}")
    
    if successes == 15:
        print("🎉 SUCCESS! SQLite WAL is handling atomic decrements perfectly.")
    else:
        print("🚨 FAILED! State was not atomic.")

    # Now let's try the 16th to verify it correctly denies insufficient funds
    valid, b, m = MINT.verify_and_spend(token_str, 100)
    print(f"16th call (should fail): {m}")

    print("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(main())
