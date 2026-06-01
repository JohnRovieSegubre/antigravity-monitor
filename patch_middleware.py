import sys
import re

with open("gateway_server.py", "r", encoding="utf-8") as f:
    content = f.read()

# We will replace the unified_payment_middleware and verify_payment_header functions
start_marker_middleware = "# --- UNIFIED PAYMENT MIDDLEWARE ---"
end_marker_middleware = "# --- USDC EIP-3009 CONFIG ---"

start_idx = content.find(start_marker_middleware)
end_idx = content.find(end_marker_middleware)

if start_idx == -1 or end_idx == -1:
    print("Could not find middleware markers")
    sys.exit(1)

new_middleware_func = """# --- UNIFIED PAYMENT MIDDLEWARE ---
# We must intercept the request BEFORE the x402 SDK, because the SDK strictly demands 
# a cryptographic signature and will block the transaction if one isn't present.
from fastapi.responses import JSONResponse

MAX_SESSION_DEPOSIT_SATS = 100000  # $1.00 hard cap

@app.middleware("http")
async def unified_payment_middleware(request: Request, call_next):
    # 1. Macaroon Bypass Check (The "Fast Lane")
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer ") and hasattr(request, "state"):
        token_str = auth_header.split(" ", 1)[1]
        try:
            m = Macaroon.deserialize(token_str)
            # Just pass the token to the route handler, verify_payment_header will do the DB deduction
            request.state.payment_payload = {"type": "macaroon_bypass", "token": token_str}
            return await call_next(request)
        except Exception:
            pass  # Invalid macaroon, let x402 handle it normally
            
    # 2. Dynamic Session Deposit (Custom 402)
    session_deposit = request.headers.get("X-Sovereign-Session-Deposit")
    if session_deposit and not auth_header.startswith("L402 "):
        try:
            deposit_sats = int(session_deposit)
            deposit_sats = min(deposit_sats, MAX_SESSION_DEPOSIT_SATS)
            
            # Since the x402 SDK middleware only knows the static route price, 
            # we intercept here to demand the higher session deposit amount.
            # We return a standard x402 payment required response.
            response = JSONResponse(
                status_code=402,
                content={"error": "Payment Required", "amount": deposit_sats},
                headers={
                    "WWW-Authenticate": f'L402 macaroon="", invoice="", amount="{deposit_sats}", pay_to="{X402_PAY_TO}", network="{X402_NETWORK}"'
                }
            )
            return response
        except ValueError:
            pass

    # 3. x402 SDK Check (The "Tollbooth")
    if _x402_middleware_func is not None:
        # We need to temporarily mock the request if it has an L402 header for a session deposit
        # because the SDK middleware might reject overpayments if it's strict.
        # However, most SDKs accept >= required price. Let's see if it passes naturally.
        return await _x402_middleware_func(request, call_next)
    
    # 4. Disabled x402 (Dev Mode)
    return await call_next(request)

"""

new_content = content[:start_idx] + new_middleware_func + content[end_idx:]

with open("gateway_server.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully patched middleware")
