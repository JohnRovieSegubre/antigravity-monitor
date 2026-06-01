"""
Sovereign MCP Server
=====================
MCP (Model Context Protocol) server for Sovereign API.
Exposes AI inference, balance checking, and model listing as MCP tools.

Works with:
- Claude Code / Claude Desktop
- Cursor
- Any MCP-compatible client

Run:
    python -m sovereign_mcp

Configure in Claude Desktop / Claude Code:
    {
        "mcpServers": {
            "sovereign": {
                "command": "python",
                "args": ["-m", "sovereign_mcp"],
                "env": {
                    "SOVEREIGN_API_KEY": "sk-sov-xxx"
                }
            }
        }
    }
"""

import json
import sys
import logging
from typing import Any

# Import the Sovereign Agent SDK
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)))
from sovereign_agent import SovereignAgent, SpendPolicy

logger = logging.getLogger("sovereign_mcp")

# ──────────────────────────────────────────────────────────────
# MCP TOOL DEFINITIONS
# ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "sovereign_chat",
        "description": (
            "Send a chat completion request to Sovereign API. "
            "Supports 200+ open and frontier AI models with crypto payment. "
            "Returns the model's response text."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The user message to send to the AI model.",
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (e.g., 'sovereign/deepseek-r1', 'sovereign/llama-4-maverick'). Defaults to 'sovereign/deepseek-r1'.",
                    "default": "sovereign/deepseek-r1",
                },
                "system": {
                    "type": "string",
                    "description": "Optional system prompt to guide the model's behavior.",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens in the response. Default: 1024.",
                    "default": 1024,
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "sovereign_balance",
        "description": (
            "Check current credit balance and today's spending on Sovereign API. "
            "Returns remaining credits, daily spend, and policy limits."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "sovereign_models",
        "description": (
            "List all available AI models on Sovereign API. "
            "Returns model IDs and pricing information."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "sovereign_topup",
        "description": (
            "Fund the Sovereign API key using x402 payment from the agent's wallet. "
            "Adds $1.00 (100,000 credits) to the balance. "
            "Requires AGENT_PRIVATE_KEY and ETH_RPC_URL to be set in the server environment."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount_usd": {
                    "type": "number",
                    "description": "Amount in USD to top up. Default: 1.0.",
                    "default": 1.0,
                }
            },
        },
    },
]


# ──────────────────────────────────────────────────────────────
# MCP SERVER (JSON-RPC over stdio)
# ──────────────────────────────────────────────────────────────

class SovereignMCPServer:
    """MCP Server implementing JSON-RPC 2.0 over stdin/stdout."""

    def __init__(self):
        self.agent = SovereignAgent()

    def handle_request(self, request: dict) -> dict:
        """Route a JSON-RPC request to the appropriate handler."""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return self._respond(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "sovereign-mcp",
                    "version": "1.0.0",
                },
            })

        elif method == "notifications/initialized":
            return None  # No response needed for notifications

        elif method == "tools/list":
            return self._respond(req_id, {"tools": TOOLS})

        elif method == "tools/call":
            return self._handle_tool_call(req_id, params)

        elif method == "ping":
            return self._respond(req_id, {})

        else:
            return self._error(req_id, -32601, f"Method not found: {method}")

    def _handle_tool_call(self, req_id: Any, params: dict) -> dict:
        """Execute a tool call."""
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if tool_name == "sovereign_chat":
                result = self._tool_chat(args)
            elif tool_name == "sovereign_balance":
                result = self._tool_balance()
            elif tool_name == "sovereign_models":
                result = self._tool_models()
            elif tool_name == "sovereign_topup":
                result = self._tool_topup(args)
            else:
                return self._error(req_id, -32602, f"Unknown tool: {tool_name}")

            return self._respond(req_id, {
                "content": [{"type": "text", "text": result}],
            })

        except Exception as e:
            return self._respond(req_id, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True,
            })

    # ──────────────────────────────────────────────────────────
    # TOOL IMPLEMENTATIONS
    # ──────────────────────────────────────────────────────────

    def _tool_chat(self, args: dict) -> str:
        """Execute a chat completion."""
        message = args.get("message", "")
        model = args.get("model", "sovereign/deepseek-r1")
        system = args.get("system")
        max_tokens = args.get("max_tokens", 1024)

        if not message:
            return "Error: 'message' is required."

        response = self.agent.chat(
            message=message,
            model=model,
            system=system,
            max_tokens=max_tokens,
        )

        if "error" in response:
            return f"Error: {response['error']}"

        # Extract content from OpenAI-compatible response
        choices = response.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            usage = response.get("usage", {})
            return f"{content}\n\n---\nModel: {model} | Tokens: {usage.get('total_tokens', '?')}"

        return json.dumps(response, indent=2)

    def _tool_balance(self) -> str:
        """Check balance and budget."""
        budget = self.agent.budget_summary()
        balance = self.agent.balance()

        lines = [
            "💰 Sovereign API Balance",
            f"   Spent Today: ${budget['spent_today_usd']:.4f}",
            f"   Requests Today: {budget['requests_today']}",
            f"   Daily Budget: ${budget['policy']['daily_budget']:.2f}",
            f"   Remaining: ${budget['policy']['remaining']:.4f}",
            f"   Emergency Halt: {'YES' if budget['policy']['emergency_halt'] else 'No'}",
        ]

        if "error" not in balance:
            lines.append(f"   API Credits: {balance}")

        return "\n".join(lines)

    def _tool_models(self) -> str:
        """List available models."""
        models = self.agent.models()

        if not models:
            return "No models available or failed to fetch model list."

        if isinstance(models, list):
            lines = ["Available Sovereign Models:", ""]
            for m in models[:50]:  # Cap at 50
                if isinstance(m, dict):
                    mid = m.get("id", "unknown")
                    lines.append(f"  • {mid}")
                else:
                    lines.append(f"  • {m}")
            if len(models) > 50:
                lines.append(f"  ... and {len(models) - 50} more")
            return "\n".join(lines)

        return json.dumps(models, indent=2)

    def _tool_topup(self, args: dict) -> str:
        """Execute a top-up."""
        amount = args.get("amount_usd", 1.0)
        result = self.agent.topup(amount_usd=amount)

        if "error" in result:
            return f"❌ Topup Failed: {result['error']}\nDetail: {result.get('detail', 'N/A')}"

        return (
            f"✅ Success! Added credits to your Sovereign API key.\n"
            f"   New Balance: {result.get('balance')} credits\n"
            f"   Tx Hash: {result.get('idempotency_key', 'Confirmed')}"
        )

    # ──────────────────────────────────────────────────────────
    # JSON-RPC HELPERS
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _respond(req_id: Any, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def main():
    """Run the MCP server in stdio mode."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,  # Log to stderr, keep stdout clean for JSON-RPC
    )

    server = SovereignMCPServer()
    logger.info("Sovereign MCP Server started (stdio mode)")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            print(json.dumps(error_resp), flush=True)
            continue

        response = server.handle_request(request)
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
