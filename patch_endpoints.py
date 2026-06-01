import sys

with open("gateway_server.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace verify_payment_header and chat_completions
# Let's find the verify_payment_header
start_marker = "async def verify_payment_header(request: Request, cost_sats: int):"
# And we'll replace down to list_models()
end_marker = "@app.get(\"/v1/models\")"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers")
    print(f"Start: {start_idx}, End: {end_idx}")
    sys.exit(1)

new_functions = """async def verify_payment_header(request: Request, cost_sats: int):
    \"\"\"
    Authentication check (Macaroon + API Key + L402).
    Returns:
        (is_valid, auth_data)
        auth_data can be:
          - {"type": "macaroon", "new_token": None, "balance": <int>}
          - {"type": "x402", "payment_payload": ..., "minted_macaroon": <str|None>}
          - {"status": 401/402, "error": ...} (Failure)
    \"\"\"

    # === CHECK 0: PAYMENT PRE-AUTHORIZED (by middleware) ===
    payment_payload = getattr(request.state, "payment_payload", None)
    if payment_payload:
        # Macaroon bypass: middleware validated the token HMAC, we need to spend from DB balance
        if isinstance(payment_payload, dict) and payment_payload.get("type") == "macaroon_bypass":
            token_str = payment_payload.get("token")
            valid, balance, msg = MINT.verify_and_spend(token_str, cost_sats)
            if valid:
                print(f"🎫 [Macaroon] Spent {cost_sats} sats (bypassed x402). Remaining: {balance}")
                return True, {"type": "macaroon", "balance": balance, "token": token_str}
            else:
                print(f"🎫 [Macaroon] Spend failed: {msg}")
                # We return string for errors so chat_completions can handle it nicely
                return False, msg
        
        # Real x402 payment (from Coinbase Facilitator)
        print(f"⚡ [x402] Payment verified by middleware — bypassing auth")
        
        # Did they pay for a session burst?
        minted_macaroon = None
        session_deposit = request.headers.get("X-Sovereign-Session-Deposit")
        if session_deposit:
            try:
                deposit_sats = int(session_deposit)
                # Cap it just in case
                deposit_sats = min(deposit_sats, 100000)
                
                # We mint a macroon, deducting the exact cost of the FIRST call immediately
                remaining = deposit_sats - cost_sats
                if remaining >= 0:
                    minted_macaroon, resulting_balance = MINT.create_session(amount_sats=remaining)
                    print(f"⚡ [x402 Session] Minted Macaroon w/ {resulting_balance} sats")
            except ValueError:
                pass
                
        return True, {"type": "x402", "payment_payload": payment_payload, "minted_macaroon": minted_macaroon}
    
    # === CHECK 1: API KEY (IDENTITY) ===
    api_key = request.headers.get("X-Sovereign-Api-Key")
    
    # Allow legacy mode (no API key required) in development
    if ENVIRONMENT == "PRODUCTION" or api_key:
        if not api_key:
            return False, {"status": 401, "error": "Missing API Key (X-Sovereign-Api-Key header)"}
        
        if not validate_key(api_key):
            return False, {"status": 401, "error": "Invalid or revoked API Key"}
        
        # Log usage
        increment_usage(api_key)
        agent_name = get_agent_name(api_key)
        print(f"🔑 [AUTH] Agent '{agent_name}' authenticated")
    
    # === CHECK 2: FUEL (MACAROON OR L402) ===
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False, "Missing Authorization"

    # CASE A: BEARER TOKEN (Macaroon) -> Usually caught by FAST LANE in middleware, but checked here as fallback
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        valid, balance, msg = MINT.verify_and_spend(token, cost_sats)
        if valid:
            return True, {"type": "macaroon", "balance": balance, "token": token}
        return False, msg

    # CASE B: LIGHTNING (L402)
    if auth_header.startswith("L402 "):
        try:
            token = auth_header.split(" ")[1]
            preimage, _ = token.split(":")

            # Dev Backdoor
            if preimage == "secret_proof_of_payment" and ENVIRONMENT != "PRODUCTION":
                return True, {"type": "lightning"}

            # Real Check
            preimage_bytes = bytes.fromhex(preimage)
            calculated_hash = hashlib.sha256(preimage_bytes).hexdigest()

            if await check_alby_payment_status(calculated_hash):
                return True, {"type": "lightning"}
            return False, "Lightning Payment Not Settled"
        except:
            return False, "Invalid L402 Format"

    return False, "Unknown Auth Type"


# --- OPENROUTER FORWARDING ---
async def forward_to_openrouter(payload: dict, route_config: dict):
    if not OPENROUTER_API_KEY:
        return JSONResponse(status_code=500, content={"error": "No API Key"})
    backend_payload = payload.copy()
    backend_payload["model"] = route_config["backend_model"]
    if "max_tokens" not in backend_payload or backend_payload["max_tokens"] > MAX_TOKENS_CAP:
        backend_payload["max_tokens"] = MAX_TOKENS_CAP

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_TITLE
    }
    
    # For streaming, we need to manually proxy to read headers early or just respond 
    # Actually, httpx is fine with Response(stream=...). But standard streaming response
    # requires StreamingResponse or proxying.
    # OpenRouter handles stream via the same endpoint.
    
    async with httpx.AsyncClient() as client:
        try:
            # We defer returning the Response object back so the caller can inject headers
            # into the initial HTTP headers (even for streams).
            
            # Since fastAPI proxy streaming can be complex, we'll return a raw httpx stream
            # if stream=True, but for simplicity here we just use the fastAPI Response
            
            req = client.build_request("POST", route_config["backend_url"], json=backend_payload, headers=headers)
            res = await client.send(req, stream=payload.get("stream", False))
            
            from fastapi.responses import StreamingResponse
            if payload.get("stream", False):
                return StreamingResponse(
                    res.aiter_raw(),
                    status_code=res.status_code,
                    media_type=res.headers.get("content-type")
                )
            else:
                await res.aread()
                return Response(
                    content=res.content,
                    status_code=res.status_code,
                    media_type=res.headers.get("content-type")
                )
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": f"Upstream Error: {e}"})


# --- ENDPOINTS ---
@app.post("/v1/chat/completions", dependencies=[Depends(rl_standard)])
async def chat_completions(request: Request):
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    requested_model = body.get("model")
    if requested_model not in MODEL_ROUTER:
        raise HTTPException(status_code=404, detail="Model not found")
    route_config = MODEL_ROUTER[requested_model]

    # Verify Payment
    is_valid, auth_data = await verify_payment_header(request, route_config["price_sats"])

    if not is_valid:
        # === 401: API KEY FAILURE ===
        if isinstance(auth_data, dict) and auth_data.get("status") == 401:
            return JSONResponse(
                status_code=401,
                content={"error": auth_data.get("error", "Invalid API Key")},
                headers={"WWW-Authenticate": "Sovereign-Api-Key"}
            )
        
        # === 403: REPLAY ATTACK / TOKEN SPENT / EXPIRED ===
        if isinstance(auth_data, str) and ("Spent" in auth_data or "expired" in auth_data or "revoked" in auth_data):
            # Also fallback to a clean 402 so they can just pay again if they want
            return JSONResponse(
                status_code=402, 
                content={"error": auth_data},
                headers={
                    "Payment-Required": "true",
                    "WWW-Authenticate": f'L402 macaroon="", invoice="", amount="{route_config["price_sats"]}", pay_to="{X402_PAY_TO}", network="{X402_NETWORK}"'
                }
            )
        
        # === 402: INSUFFICIENT FUNDS (Top-Up Flow) ===
        if isinstance(auth_data, str) and "Insufficient Funds" in auth_data:
            # Here, the token is valid but empty.
            # In V6, if empty, the agent should just fall back to standard 402.
            # They just pay exactly what it costs from their wallet. 
            return JSONResponse(
                status_code=402, 
                content={"error": "Insufficient Funds in Macaroon"},
                headers={
                    "Payment-Required": "true",
                    "WWW-Authenticate": f'L402 macaroon="", invoice="", amount="{route_config["price_sats"]}", pay_to="{X402_PAY_TO}", network="{X402_NETWORK}"'
                }
            )

        # === 402: LEGACY L402 INVOICE (If x402 disabled) ===
        p_hash, invoice = await generate_real_invoice(route_config["price_sats"], f"Sovereign: {requested_model}")
        return JSONResponse(
            status_code=402,
            content={"error": "Payment Required", "invoice": invoice, "price_sats": route_config["price_sats"]},
            headers={"WWW-Authenticate": "L402 token", "X-L402-Invoice": invoice}
        )

    # Execute
    response = await forward_to_openrouter(body, route_config)

    # V6 BALANCES: Inject Headers
    # Case A: Existing Session
    if isinstance(auth_data, dict) and auth_data.get("type") == "macaroon":
        response.headers["X-Sovereign-Macaroon-Balance"] = str(auth_data.get("balance", 0))

    # Case B: Newly Minted Session
    if isinstance(auth_data, dict) and auth_data.get("type") == "x402":
        minted_macaroon = auth_data.get("minted_macaroon")
        if minted_macaroon:
            response.headers["X-Sovereign-Macaroon"] = minted_macaroon

        payload = auth_data.get("payment_payload")
        if payload:
            try:
                receipt_json = json.dumps(payload if isinstance(payload, dict) else str(payload))
                encoded_receipt = base64.b64encode(receipt_json.encode()).decode()
                response.headers["PAYMENT-RESPONSE"] = encoded_receipt
            except Exception:
                pass  # Non-critical

    return response


@app.post("/v1/macaroon/revoke")
async def revoke_macaroon(request: Request):
    \"\"\"Instantly revokes a Macaroon session.\"\"\"
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer Macaroon required")
        
    token_str = auth_header.split(" ", 1)[1]
    
    try:
        m = Macaroon.deserialize(token_str)
        m_id = m.identifier
        if isinstance(m_id, bytes):
            m_id = m_id.decode('utf-8')
            
        v = Verifier()
        if not v.verify(m, MINT_SECRET): 
            raise HTTPException(status_code=401, detail="Invalid Signature")

        with MINT._get_db() as conn:
            conn.execute("UPDATE macaroons SET revoked = 1 WHERE id = ?", (m_id,))
            conn.commit()
            
        return {"status": "success", "message": "Macaroon revoked"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""

new_content = content[:start_idx] + new_functions + content[end_idx:]

with open("gateway_server.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully patched verify_payment_header, forward_to_openrouter, chat_completions, and revoke_macaroon")
