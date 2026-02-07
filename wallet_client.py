import httpx
import time
import sys

GATEWAY_URL = "http://localhost:8000/v1/chat/completions"
# MOCK CONSTANTS (Must match server)
MOCK_PREIMAGE = "secret_proof_of_payment"

def log(msg):
    print(f"[WALLET] {msg}")

def buy_compute_mock():
    log(f"Attempting to buy compute from {GATEWAY_URL}")
    
    payload = {
        "model": "sovereign-llama3-70b", 
        "messages": [{"role": "user", "content": "Hello, Machine Economy! Tell me a secret about the future."}]
    }

    try:
        # 1. Try to buy (Expecting 402)
        resp = httpx.post(GATEWAY_URL, json=payload, timeout=60.0)
        
        if resp.status_code == 200:
            log("Wait... it was free? (Unexpected)")
            log(resp.json())
            return

        if resp.status_code == 402:
            log("[PAYMENT_REQUIRED] 402 Received.")
            data = resp.json()
            
            invoice = data.get("invoice")
            challenge = data.get("challenge")
            price = data.get("price_sats")
            
            log(f"   Invoice: {invoice[:10]}...")
            log(f"   Price:   {price} sats")
            
            # 2. PAY THE BILL (Mock)
            log("Paying Invoice via Lightning (Simulated)...")
            time.sleep(1.0) # Simulate network lag
            preimage = MOCK_PREIMAGE
            
            # 3. SIGN THE CHALLENGE (Mock)
            signature = f"signed_{challenge}"
            
            # 4. CONSTRUCT L402 TOKEN
            # Format: L402 <Preimage>:<Signature>
            token = f"L402 {preimage}:{signature}"
            
            log("Authorization Token Generated.")
            
            # 5. RETRY WITH AUTH
            log("Resending Request with Auth Header...")
            resp2 = httpx.post(
                GATEWAY_URL, 
                json=payload,
                headers={"Authorization": token},
                timeout=120.0
            )
            
            if resp2.status_code == 200:
                log("SUCCESS! Compute Acquired.")
                log(f"   Response: {resp2.json()}")
            else:
                log(f"Failed Retry: {resp2.status_code} - {resp2.text}")
                sys.exit(1)
                
        else:
            log(f"Unexpected Error: {resp.status_code}")
            sys.exit(1)

    except Exception as e:
        log(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    buy_compute_mock()
