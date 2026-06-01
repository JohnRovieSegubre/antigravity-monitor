# How to Connect OpenClaw to Sovereign API

*OpenClaw agents can now call LLMs via Sovereign API's **x402 pay-per-request mode**. This guide shows how to configure OpenClaw's provider to use `https://api.sovereign-api.com/v1` and your agent's wallet key. In this setup, when an agent calls OpenAI endpoints, Sovereign API will issue a "402 Payment Required" response and the OpenClaw agent can automatically send a USDC micropayment on Base to continue the request.*


*Published: February 27, 2026*

OpenClaw is one of the most popular open-source agent orchestrators. It supports multiple LLM providers through OpenAI-compatible APIs — and Sovereign API is now a first-class citizen.

This guide walks you through connecting OpenClaw to Sovereign API, including the configuration gotchas that will save you hours of debugging.

## Prerequisites

- Node.js 18+
- OpenClaw installed (`npm install -g openclaw`)
- A Sovereign API key ([register here](https://api.sovereign-api.com/v1/register))

## Step 1: Configure the Provider

Add Sovereign to your `~/.openclaw/openclaw.json` under `models.providers`:

```json
"sovereign": {
  "baseUrl": "https://api.sovereign-api.com/v1",
  "apiKey": "${SOVEREIGN_API_KEY}",
  "api": "openai-completions",
  "models": [
    {
      "id": "sovereign/gpt-5.2-chat",
      "name": "Sovereign GPT-5.2",
      "reasoning": false,
      "input": ["text"],
      "contextWindow": 1000000,
      "maxTokens": 8192
    },
    {
      "id": "sovereign/deepseek-r1",
      "name": "Sovereign DeepSeek R1",
      "reasoning": true,
      "input": ["text"],
      "contextWindow": 128000,
      "maxTokens": 8192
    }
  ]
}
```

> **⚠️ Critical:** The `baseUrl` must end with `/v1`. OpenClaw's internal OpenAI SDK automatically appends `/chat/completions` to the base URL. If you omit `/v1`, requests will hit the wrong path and you will get blank responses.

## Step 2: Set Your API Key

Add your key to `~/.openclaw/.env`:

```
SOVEREIGN_API_KEY=sk-sov-your-key-here
```

## Step 3: Set the Default Model

```bash
npx openclaw config set agents.defaults.model.primary sovereign/gpt-5.2-chat
```

## Step 4: Run

```bash
npx openclaw gateway start
npx openclaw tui
```

Type a message and watch it stream back from Sovereign API.

## How It Works Under the Hood

When you send a message in OpenClaw:

1. **OpenClaw Gateway** receives your message via WebSocket
2. **Pi (OpenClaw's LLM engine)** formats it as an OpenAI Chat Completions request
3. The request hits `https://api.sovereign-api.com/v1/chat/completions`
4. **Sovereign API** routes to the configured backend model via OpenRouter
5. **The SSE Normalizer** strips non-standard fields from the response stream
6. OpenClaw receives a clean, spec-compliant stream and renders the text

### Why the SSE Normalizer Matters

Sovereign API proxies requests through OpenRouter, which supports 280+ models. However, OpenRouter adds proprietary fields to their SSE (Server-Sent Events) streams:

- `provider: "OpenAI"` — identifies the upstream provider
- `native_finish_reason: "stop"` — provider-specific finish reason
- `cost`, `is_byok`, `cost_details` — billing metadata

These fields are not part of the official OpenAI specification. Strict clients like OpenClaw's internal parser will silently reject chunks containing non-standard fields, resulting in blank responses.

Sovereign API's built-in normalizer intercepts every chunk, strips non-standard fields, and forwards only spec-compliant JSON. This guarantees compatibility with any OpenAI-compatible client.

## Troubleshooting

### Blank Bubbles / No Response Text
**Cause:** The most common cause is a missing `/v1` in the `baseUrl`. Without it, requests hit the wrong endpoint.

**Fix:** Ensure your `baseUrl` is `https://api.sovereign-api.com/v1` (not `https://api.sovereign-api.com`).

### Credits Deducted But No Text Displayed
**Cause:** The `api` field in the provider config is wrong or missing.

**Fix:** Ensure `"api": "openai-completions"` is set in the sovereign provider block.

### Connection Refused
**Cause:** The OpenClaw gateway is not running.

**Fix:** Run `npx openclaw gateway start` before launching the TUI or Web UI.

### Model Not Found
**Cause:** The model ID doesn't match any registered model.

**Fix:** Check available models with `curl https://api.sovereign-api.com/v1/models` and use the exact `sovereign/model-name` format.

---

## Available Models

Sovereign API provides access to 280+ models. Popular choices for OpenClaw:

| Model | Best For | Reasoning |
|-------|---------|-----------|
| `sovereign/gpt-5.2-chat` | General conversation, coding | No |
| `sovereign/deepseek-r1` | Complex reasoning, math | Yes |
| `sovereign/claude-3.7-sonnet` | Writing, analysis | No |
| `sovereign/llama-3.3-70b-instruct` | Budget-friendly tasks | No |

Browse all models: `curl https://api.sovereign-api.com/v1/models`

---

*Sovereign API: Give your AI a wallet, not a credit card.*
