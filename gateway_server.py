# gateway_server.py
import time
import httpx
import os
import json
import uvicorn
import socket
import sys
import requests
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
# from dotenv import load_dotenv # Optional if using .env

app = FastAPI(title="Sovereign AI Gateway (Phase 3: OpenRouter dropshipping)")

# --- CONFIGURATION ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEVELOPMENT") # "PRODUCTION" disables backdoor
MAX_TOKENS_CAP = 1024 # Safety Constraint (Gemini)
SITE_URL = "https://sovereign-gateway.local" # Required by OpenRouter
SITE_TITLE = "Sovereign Shadow Node"

# Load Secrets
SECURE_DIR = Path(r"c:\Users\rovie segubre\.gemini\antigravity\playground\obsidian-trifid\.agent\secure")
ALBY_TOKEN_FILE = SECURE_DIR / "alby_token.json"
OPENROUTER_KEY_FILE = SECURE_DIR / "openrouter_key.json"

ALBY_ACCESS_TOKEN = None
OPENROUTER_API_KEY = None

try:
    if ALBY_TOKEN_FILE.exists():
        with open(ALBY_TOKEN_FILE, 'r') as f:
            ALBY_ACCESS_TOKEN = json.load(f).get("ALBY_ACCESS_TOKEN")
    
    if OPENROUTER_KEY_FILE.exists():
        with open(OPENROUTER_KEY_FILE, 'r') as f:
            OPENROUTER_API_KEY = json.load(f).get("OPENROUTER_API_KEY")
except Exception as e:
    print(f"[ERROR] Failed to load secrets: {e}")

if not OPENROUTER_API_KEY:
    print("[WARN] OpenRouter Key Missing! Gateway will fail to generate intelligence.")


MODEL_ROUTER = {
    # Public Model Name -> Backend Provider config
    "sovereign-llama3-70b": {
        "backend_url": "https://openrouter.ai/api/v1/chat/completions",
        "backend_model": "meta-llama/llama-3.3-70b-instruct",
        "price_sats": 50
    },
    "sovereign-r1": {
        "backend_url": "https://openrouter.ai/api/v1/chat/completions",
        "backend_model": "deepseek/deepseek-r1",
        "price_sats": 10
    },
    "sovereign-gpt4o": {
        "backend_url": "https://openrouter.ai/api/v1/chat/completions",
        "backend_model": "openai/gpt-4o",
        "price_sats": 100 # High Value Asset
    }
}

# --- ALBY LOGIC ---
INVOICE_DB = {} # payment_hash -> {status: 'pending'}

async def generate_real_invoice(price_sats: int, description: str):
    if not ALBY_ACCESS_TOKEN:
        return "mock_hash", "lnbc_mock_invoice_missing_token"

    url = "https://api.getalby.com/invoices"
    headers = {"Authorization": f"Bearer {ALBY_ACCESS_TOKEN}"}
    payload = {"amount": price_sats, "description": description}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                data = response.json()
                p_hash = data['payment_hash']
                INVOICE_DB[p_hash] = {"status": "pending"}
                return p_hash, data['payment_request']
            else:
                print(f"[ALBY ERROR] {response.text}")
        except Exception as e:
            print(f"[ALBY EXCEPTION] {e}")
    return None, None

# --- L402 MIDDLEWARE ---
async def verify_l402_header(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("L402"):
        return False, "Missing L402 header"

    try:
        token = auth_header.split(" ")[1]
        preimage, _ = token.split(":")
    except ValueError:
        return False, "Invalid token format"

    # --- SAFETY SWITCH (BACKDOOR) ---
    if preimage == "secret_proof_of_payment":
        if ENVIRONMENT == "PRODUCTION":
            return False, "Dev Backdoor Disabled in PRODUCTION"
        return True, "Authorized (Dev Backdoor)"

    # Real verification pending (requires hashing preimage & checking DB)
    return False, "Real Payment Verification Not Implemented Yet"

# --- OPENROUTER FORWARDING ---
async def forward_to_openrouter(payload: dict, route_config: dict):
    """Forwards request to OpenRouter with Safety Caps."""
    if not OPENROUTER_API_KEY:
        return JSONResponse(status_code=500, content={"error": "Gateway missing OpenRouter Key"})

    # 1. Prepare Payload
    backend_payload = payload.copy()
    backend_payload["model"] = route_config["backend_model"]
    
    # 2. Enforce Safety Cap (Gemini Requirement)
    if "max_tokens" not in backend_payload or backend_payload["max_tokens"] > MAX_TOKENS_CAP:
        backend_payload["max_tokens"] = MAX_TOKENS_CAP
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL, # OpenRouter Requirement
        "X-Title": SITE_TITLE     # OpenRouter Requirement
    }

    print(f"[GATEWAY] Forwarding to OpenRouter: {route_config['backend_model']}")
    
    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.post(
                route_config["backend_url"],
                json=backend_payload,
                headers=headers,
                timeout=120.0 
            )
            duration = time.time() - start_time
            print(f"[GATEWAY] OpenRouter Response: {response.status_code} ({duration:.2f}s)")
            
            # Proxy the response back exactly as received
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type")
            )
        except Exception as e:
             print(f"[GATEWAY ERROR] OpenRouter Connect Failed: {e}")
             return JSONResponse(status_code=502, content={"error": "Upstream Provider Failed"})


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
        requested_model = body.get("model")
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if requested_model not in MODEL_ROUTER:
        raise HTTPException(status_code=404, detail="Model not found")
    
    route_config = MODEL_ROUTER[requested_model]

    # L402 GUARD
    is_valid, error_msg = await verify_l402_header(request)
    
    if not is_valid:
        # 402 PAYMENT REQUIRED
        challenge = f"sign_{int(time.time())}"
        p_hash, invoice = await generate_real_invoice(route_config["price_sats"], f"Sovereign: {requested_model}")
        
        if not invoice: invoice = "error_generating_invoice"
        
        headers = {
            "WWW-Authenticate": "L402 token",
            "X-L402-Invoice": invoice,
            "X-L402-Challenge": challenge
        }
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "invoice": invoice,
                "price_sats": route_config["price_sats"]
            },
            headers=headers
        )

    # PAID -> EXECUTE
    return await forward_to_openrouter(body, route_config)

@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": k, "price": v["price_sats"]} for k,v in MODEL_ROUTER.items()]}

if __name__ == "__main__":
    PORT = 8000
    
    # Idempotency Check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', PORT))
    sock.close()
    
    if result == 0:
        try:
             resp = requests.get(f"http://127.0.0.1:{PORT}/docs", timeout=5.0)
             if resp.status_code == 200:
                 print("[INFO] Gateway already running.")
                 sys.exit(0)
        except:
             pass

    print(f"Sovereign Shadow Node (OpenRouter Active) starting on {PORT}...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except SystemExit: pass
    except Exception as e:
        if "10048" in str(e): sys.exit(0)
        raise e
