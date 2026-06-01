# Sovereign Agent SDK

> The reference agent runtime for Sovereign API.  
> Auto-wallet · Auto-payment · Policy enforcement · Budget tracking

---

## Install

```bash
pip install sovereign-agent

# With x402 auto-payment support
pip install sovereign-agent[x402]
```

---

## Quickstart

```python
from sovereign_agent import SovereignAgent

agent = SovereignAgent(api_key="sk-sov-xxx")
response = agent.chat("What is quantum computing?")
print(response["choices"][0]["message"]["content"])
```

That's it. The SDK handles wallet generation, payment negotiation, and budget tracking automatically.

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SOVEREIGN_API_KEY` | Prepaid API key (`sk-sov-...`) | None |
| `SOVEREIGN_BASE_URL` | Gateway URL | `https://api.sovereign-api.com/v1` |
| `GATEWAY_URL` | Alias for base URL | None |
| `OPENAI_API_KEY` | Fallback for API key (OpenAI compat) | None |

### Constructor Parameters

```python
agent = SovereignAgent(
    api_key="sk-sov-xxx",            # Or set SOVEREIGN_API_KEY env var
    base_url="https://api...",        # Gateway URL
    private_key="0x...",              # Explicit private key (optional)
    policy=SpendPolicy(...),          # Custom spend policy
    budget_limit=5.00,               # Daily budget in USD (shortcut)
    model="sovereign/deepseek-r1",   # Default model
    auto_wallet=True,                # Auto-generate wallet (default: True)
)
```

---

## API Reference

### `agent.chat(message, model=None, system=None, max_tokens=None, temperature=None)`

Send a chat completion request.

```python
response = agent.chat("Explain recursion", model="sovereign/llama-4-maverick")
print(response["choices"][0]["message"]["content"])
```

**Returns:** OpenAI-compatible response dict.

### `agent.chat_stream(message, model=None, system=None, max_tokens=None, temperature=None)`

Stream a chat completion. Yields content chunks.

```python
for chunk in agent.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### `agent.chat_multi(messages, model=None, stream=False)`

Multi-turn conversation with a list of message dicts.

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]
response = agent.chat_multi(messages)
```

### `agent.balance()`

Check remaining API credits.

```python
print(agent.balance())
# → {"credits_remaining": 95000, "credits_used": 5000}
```

### `agent.models()`

List available models.

```python
for model in agent.models():
    print(model["id"])
```

### `agent.budget_summary()`

Get today's spending summary with policy limits.

```python
print(agent.budget_summary())
# → {
#     "date": "2026-03-14",
#     "spent_today_usd": 0.0042,
#     "requests_today": 3,
#     "policy": {
#         "daily_budget": 5.00,
#         "max_per_request": 0.05,
#         "remaining": 4.9958,
#         "emergency_halt": False
#     }
# }
```

### `agent.halt()` / `agent.resume()`

Emergency kill switch. Freezes all spending immediately.

```python
agent.halt()    # All requests return BLOCKED
agent.resume()  # Normal operation resumes
```

---

## Policy Enforcement

Mechanical safety — enforced in code, not in prompts.

```python
from sovereign_agent import SovereignAgent, SpendPolicy

policy = SpendPolicy(
    max_spend_per_request=0.05,   # $0.05 cap per request
    daily_budget=5.00,            # $5.00 total per day
    allowed_models=[              # Only these models allowed
        "sovereign/deepseek-r1",
        "sovereign/llama-4-maverick",
    ],
    emergency_halt=False,         # Kill switch
)

agent = SovereignAgent(policy=policy)
```

### What Gets Blocked

| Check | Trigger | Error |
|-------|---------|-------|
| Emergency halt | `emergency_halt=True` | `BLOCKED: Emergency halt is active` |
| Model allowlist | Model not in `allowed_models` | `BLOCKED: Model not in allowed list` |
| Per-request cap | Estimated cost > `max_spend_per_request` | `BLOCKED: Exceeds per-request cap` |
| Daily budget | `spent_today >= daily_budget` | `BLOCKED: Daily budget exhausted` |

All checks happen **before** the request leaves your machine.

---

## Wallet Management

On first run, the SDK auto-generates an EVM wallet:

```
~/.sovereign/
├── wallet.json    # Private key + address (chmod 600)
├── config.json    # API key, gateway URL
└── budget.json    # Daily spend tracking
```

### Manual Wallet

```python
from sovereign_agent import SovereignWallet

# Use existing key
wallet = SovereignWallet(private_key="0xabc...")
print(wallet.address)  # 0x...

# Or let it auto-generate
wallet = SovereignWallet()
print(wallet.address)  # New address, persisted to ~/.sovereign/wallet.json
```

---

## Auto-402 Payment

When the gateway returns HTTP 402 (Payment Required), the SDK:

1. Detects the `PAYMENT-REQUIRED` header
2. Signs a USDC micro-payment using the agent's wallet
3. Retries the original request with the signed payment
4. Records the spend in the budget tracker

This is invisible to the caller. You call `agent.chat()` and get a response.

**Requirements for auto-pay:**
```bash
pip install sovereign-agent[x402]
```

The wallet must hold USDC on Base (eip155:8453).

---

## Error Handling

All methods return dicts. Errors are in the `"error"` key:

```python
response = agent.chat("Hello")

if "error" in response:
    print(f"Failed: {response['error']}")
else:
    print(response["choices"][0]["message"]["content"])
```

---

## Logging

The SDK uses Python's `logging` module:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs:
# INFO:sovereign_agent.wallet:Wallet loaded: 0x...
# INFO:sovereign_agent:SovereignAgent initialized | gateway=... | budget=$5.00/day
# INFO:sovereign_agent:Chat OK | model=sovereign/deepseek-r1 | tokens=142
```
