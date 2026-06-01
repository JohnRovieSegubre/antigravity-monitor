# Sovereign MCP Server

> MCP server for Sovereign API — expose 299+ AI models as tools for Claude Code, Cursor, and any MCP-compatible client.

---

## Install

```bash
pip install sovereign-agent
```

The MCP server is included in the `sovereign-agent` package.

---

## Setup

### Claude Code / Claude Desktop

Add to your MCP config file (`~/.claude/mcp.json` or project `.mcp.json`):

```json
{
    "mcpServers": {
        "sovereign": {
            "command": "python",
            "args": ["-m", "sovereign_mcp"],
            "env": {
                "SOVEREIGN_API_KEY": "sk-sov-your-key-here"
            }
        }
    }
}
```

### Cursor

Add to Cursor settings → MCP Servers:

```json
{
    "sovereign": {
        "command": "python",
        "args": ["-m", "sovereign_mcp"],
        "env": {
            "SOVEREIGN_API_KEY": "sk-sov-your-key-here"
        }
    }
}
```

### Manual Start

```bash
export SOVEREIGN_API_KEY=sk-sov-xxx
python -m sovereign_mcp
```

The server communicates via JSON-RPC 2.0 over stdin/stdout (MCP stdio transport).

---

## Available Tools

### `sovereign_chat`

Send a chat completion to any of 299+ models.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | ✅ | The user message |
| `model` | string | ❌ | Model ID (default: `sovereign/deepseek-r1`) |
| `system` | string | ❌ | System prompt |
| `max_tokens` | integer | ❌ | Max response tokens (default: 1024) |

**Example prompt in Claude Code:**
> "Use the sovereign_chat tool to ask deepseek-r1 to explain quantum entanglement"

### `sovereign_balance`

Check current credit balance and today's spending.

No parameters required. Returns:
- Spent today (USD)
- Requests today
- Daily budget limit
- Remaining budget
- Emergency halt status

### `sovereign_models`

List all available AI models with their IDs.

No parameters required. Returns up to 50 model IDs.

---

## How It Works

```
Claude Code → JSON-RPC request → sovereign_mcp → sovereign_agent SDK → Sovereign API
                                                  ↑
                                          auto-wallet, auto-402,
                                          policy, budget tracking
```

The MCP server uses `sovereign_agent.SovereignAgent` internally, inheriting all features:

- **Auto-wallet:** EVM wallet at `~/.sovereign/wallet.json`
- **Auto-402:** Automatic USDC payment signing
- **Policy:** Spend caps and model allowlists
- **Budget:** Daily spend tracking

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SOVEREIGN_API_KEY` | Your `sk-sov-...` key | Required |
| `SOVEREIGN_BASE_URL` | Gateway URL | `https://api.sovereign-api.com/v1` |

---

## Getting an API Key

```bash
curl -X POST https://api.sovereign-api.com/v1/register \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent"}'

# → {"api_key": "sk-sov-abc123..."}
```

Fund it:
```bash
curl -X POST https://api.sovereign-api.com/v1/key/topup \
  -H "Authorization: Bearer sk-sov-abc123..."
# $1 USDC = 100,000 credits
```
