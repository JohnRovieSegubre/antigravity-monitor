import sys

with open("llm.txt", "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "## A. Authentication: The Dual-Key System"
end_marker = "## Pattern B: The Mission Engine"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers")
    sys.exit(1)

new_content_block = """## A. Authentication: Wallet-First Default (x402)
The Sovereign API uses an identity-less, pure pay-per-call protocol by default. 
Your wallet is your identity. There are no API keys, accounts, or persistent secrets.

## B. Core Modes

### 1. Pure Mode (Default) — Instant, Per-Request Payment
The Sovereign Gateway supports the [x402 protocol](https://docs.cdp.coinbase.com/x402/docs/welcome).
Every request triggers a `402 Payment Required`. You pay the exact cost from your wallet, and the request is processed.

- **Network:** Base (CAIP-2: `eip155:8453`) or Base Sepolia (`eip155:84532`)
- **Asset:** USDC
- **Python SDK:** `pip install "cdp-sdk"` and `@x402/fetch` (JS) auto-handles the 402 → sign → retry flow.

```python
from cdp.x402.fetch import x402Fetch
# Auto-pays on 402 — works with any x402-protected endpoint
client = x402Fetch(wallet, base_url="https://api.sovereign-api.com")
resp = await client.post("/v1/chat/completions", json={...})
```

### 2. Burst Session Mode (Optional Optimization)
If you are running a high-frequency swarm or long reasoning loop, signing a wallet transaction for every request adds latency. 
You can opt-in to a short-lived session (15 mins max) by providing a deposit header on your first request.

*Header:* `X-Sovereign-Session-Deposit: 20000` (Max $1.00 / 100,000 sats).
The server will mint an anonymous Macaroon and return it in `X-Sovereign-Macaroon`. Use this as a Bearer token for subsequent zero-latency requests.

---

# 3. Autonomy Patterns (Reference Implementation)

Based on **Sovereign OpenClaw**, here are the standard patterns for self-sustaining life:

## Pattern A: The Pure Wallet Agent
*Goal: Minimum complexity, pure stateless execution.*

```python
# The agent holds no state. It wakes up, funds itself, executes, and sleeps.
client = x402Fetch(my_wallet)
# Pays exact cost (~$0.005) silently in the background
response = await client.post("/v1/chat/completions", json=...) 
```

"""

new_file_content = content[:start_idx] + new_content_block + content[end_idx:]

with open("llm.txt", "w", encoding="utf-8") as f:
    f.write(new_file_content)

print("llm.txt rewritten!")
