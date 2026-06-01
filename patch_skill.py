import sys

with open("landing/skill.md", "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "## What Is This?"
end_marker = "## Available Models (299+ Supported)"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers")
    sys.exit(1)

new_content_block = """## What Is This?

Sovereign Intelligence API is an **OpenAI-compatible inference endpoint** where AI agents pay with cryptocurrency instead of credit cards.

**Why it exists:** Most AI APIs require a human with a credit card. Sovereign API removes that — your agent can pay for its own compute natively using the x402 protocol (USDC on Base).

**Compatibility:** Drop-in replacement for OpenAI's `/v1/chat/completions` endpoint.

---

## Guest Mode: Pure Wallet-First x402 (Default)

Guest Mode is now **identical to x402engine** by default — just fund your wallet and go. The Sovereign API is a pure pay-per-call API.

- No API keys
- No accounts
- No bearer tokens
- No extra secrets
- Wallet payment = authentication

### Pure Mode (Recommended for most sovereign agents)

For standard, single-shot agent requests, you just use the official `@x402/fetch` client. Every request triggers an exact-cost 402, your wallet pays it instantly, and the request completes.

**Python Example:**
```python
from cdp.x402.fetch import x402Fetch

# Automatically intercepts 402s and signs payments using your wallet
client = x402Fetch(wallet_signer, base_url="https://api.sovereign-api.com")

response = await client.post("/v1/chat/completions", json={
    "model": "sovereign/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Analyze this data."}]
})
```

---

## Burst Session Mode (Optional Optimization)

Want zero-latency for long agent loops? Add one header on the first call.

For swarms or long reasoning loops doing 20+ rapid parallel tool calls, signing an on-chain transaction for *every single call* adds 2-3 seconds of latency each time. **Burst Session Mode** allows you to optionally deposit a slightly larger amount upfront (e.g., $0.20) to receive an anonymous session Macaroon for native zero-latency streaming.

*Note: Sessions are intentionally short-lived (15 min default) and low-value ($1.00 max cap). They are an optimization for tool-heavy bursts, not a required persistent account.*

### 1. The SovereignX402 SDK Wrapper
Drop this 35-line wrapper into your agent's codebase for perfect DX:

**Python (httpx):**
```python
import httpx
import asyncio
from typing import Optional, Dict

class SovereignX402:
    def __init__(self, wallet_signer, base_url: str = "https://api.sovereign-api.com",
                 session_deposit_sats: int = 0):  # 0 = pure per-call mode
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.wallet = wallet_signer  # Integration with your preferred CDP/EVM signer
        self.session_deposit_sats = session_deposit_sats
        self.macaroon: Optional[str] = None

    async def post(self, path: str, json: dict, stream: bool = False):
        headers: Dict[str, str] = {}
        if self.macaroon:
            headers["Authorization"] = f"Bearer {self.macaroon}"
        elif self.session_deposit_sats:
            headers["X-Sovereign-Session-Deposit"] = str(self.session_deposit_sats)

        resp = await self.client.post(path, json=json, headers=headers)

        if resp.status_code == 402:
            # @x402/fetch style auto-payment happens here using self.wallet
            # ... process payment ...
            
            # Catch the new Macaroon from the retry response
            retry_resp = await self.client.post(path, json=json, headers=headers)
            if "X-Sovereign-Macaroon" in retry_resp.headers:
                self.macaroon = retry_resp.headers["X-Sovereign-Macaroon"]
            return retry_resp

        if "X-Sovereign-Macaroon" in resp.headers:
            self.macaroon = resp.headers["X-Sovereign-Macaroon"]

        return resp
```

**JavaScript (@x402/fetch):**
```js
import x402Fetch from '@x402/fetch';

export function createSovereignClient(wallet, sessionDepositSats = 0) {
  const base = x402Fetch({ wallet, baseURL: 'https://api.sovereign-api.com' });
  let macaroon = null;

  return {
    async post(path, body) {
      const headers = macaroon ? { Authorization: `Bearer ${macaroon}` } : {};
      if (sessionDepositSats && !macaroon) {
        headers['X-Sovereign-Session-Deposit'] = sessionDepositSats.toString();
      }

      let res = await base.post(path, body, { headers });

      if (res.status === 402) {
        res = await base.post(path, body, { headers }); // auto-pays
        if (res.headers['x-sovereign-macaroon']) {
          macaroon = res.headers['x-sovereign-macaroon'];
        }
      }
      return res;
    }
  };
}
```

### 2. Security Warning
⚠️ **Macaroons are anonymous, transferable bearer tokens carrying real money.**
They are NOT cryptographically tied to your wallet address. Anyone holding the session Macaroon string can spend your remaining burst balance. **Treat them like private keys. Never log them.**

If you want to manually kill a session early, hit `POST /v1/macaroon/revoke` with the Macaroon as your Bearer token.

---

"""

new_file_content = content[:start_idx] + new_content_block + content[end_idx:]

with open("landing/skill.md", "w", encoding="utf-8") as f:
    f.write(new_file_content)

print("skill.md rewritten!")
