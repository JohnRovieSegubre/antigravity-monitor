"""
Sovereign Agent — Agent-Native Client
=======================================
The reference agent runtime for Sovereign API.

Zero-config initialization:
    agent = SovereignAgent()
    response = agent.chat("Hello, world!")

Features:
- Auto-wallet generation (no human setup)
- Auto-402 payment handling (x402 USDC)
- Policy enforcement (spend caps, daily budgets)
- Budget tracking (persistent)
- Streaming support (SSE)
- Structured logging (no emoji spam)
"""

import json
import logging
import os
import time
from typing import Iterator, Optional

import requests

from .wallet import SovereignWallet, load_config, save_config
from .policy import SpendPolicy, PolicyEnforcer, BudgetTracker

logger = logging.getLogger("sovereign_agent")

# Default gateway URL
DEFAULT_GATEWAY = "https://api.sovereign-api.com/v1"

# Optional: x402 auto-pay
try:
    from x402 import x402ClientSync
    from x402.http.clients import x402_requests
    from x402.mechanisms.evm import EthAccountSigner
    from x402.mechanisms.evm.exact.register import register_exact_evm_client
    _X402_AVAILABLE = True
except ImportError:
    _X402_AVAILABLE = False


class SovereignAgent:
    """
    The canonical agent runtime for Sovereign API.

    Usage:
        from sovereign_agent import SovereignAgent

        agent = SovereignAgent(budget_limit=5.00)
        response = agent.chat("What is quantum computing?")
        print(response["choices"][0]["message"]["content"])

        # Streaming
        for chunk in agent.chat_stream("Tell me a story"):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        private_key: str = None,
        policy: SpendPolicy = None,
        budget_limit: float = None,
        model: str = "sovereign/deepseek-r1",
        auto_wallet: bool = True,
    ):
        # --- Gateway URL ---
        self.base_url = (
            base_url
            or os.getenv("SOVEREIGN_BASE_URL")
            or os.getenv("GATEWAY_URL")
            or DEFAULT_GATEWAY
        ).rstrip("/")

        # --- API Key (prepaid sk-sov-...) ---
        self.api_key = (
            api_key
            or os.getenv("SOVEREIGN_API_KEY")
            or os.getenv("OPENAI_API_KEY")  # Compatible with OpenAI env var
        )

        # --- Wallet (auto-generate if needed) ---
        if private_key:
            self.wallet = SovereignWallet(private_key=private_key)
        elif auto_wallet:
            self.wallet = SovereignWallet()
        else:
            self.wallet = None

        # --- Policy ---
        if policy:
            self.policy = policy
        else:
            self.policy = SpendPolicy(
                daily_budget=budget_limit if budget_limit else 5.00
            )
        self._enforcer = PolicyEnforcer(self.policy)

        # --- Default Model ---
        self.default_model = model

        # --- Session ---
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "SovereignAgent/1.0",
        })

        # Log init
        logger.info(
            "SovereignAgent initialized | gateway=%s | key=%s | wallet=%s | budget=$%.2f/day",
            self.base_url,
            f"{self.api_key[:14]}..." if self.api_key else "none",
            self.wallet.address[:10] + "..." if self.wallet else "none",
            self.policy.daily_budget,
        )

    # ──────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        model: str = None,
        system: str = None,
        max_tokens: int = None,
        temperature: float = None,
        **kwargs,
    ) -> dict:
        """
        Send a chat completion request. Returns the full OpenAI-compatible response dict.

        Args:
            message: The user message.
            model: Model to use (default: self.default_model).
            system: Optional system prompt.
            max_tokens: Max tokens in response.
            temperature: Sampling temperature.

        Returns:
            dict: OpenAI-compatible response with choices, usage, etc.
        """
        model = model or self.default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        return self._request(model=model, messages=messages, stream=False,
                             max_tokens=max_tokens, temperature=temperature, **kwargs)

    def chat_stream(
        self,
        message: str,
        model: str = None,
        system: str = None,
        max_tokens: int = None,
        temperature: float = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        Stream a chat completion. Yields content chunks as strings.

        Usage:
            for chunk in agent.chat_stream("Tell me a joke"):
                print(chunk, end="", flush=True)
        """
        model = model or self.default_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        yield from self._request_stream(model=model, messages=messages,
                                         max_tokens=max_tokens, temperature=temperature, **kwargs)

    def chat_multi(
        self,
        messages: list,
        model: str = None,
        stream: bool = False,
        **kwargs,
    ):
        """
        Send a multi-turn conversation (list of message dicts).
        
        Args:
            messages: List of {"role": "...", "content": "..."} dicts.
            model: Model to use.
            stream: Whether to stream.
        """
        model = model or self.default_model
        if stream:
            return self._request_stream(model=model, messages=messages, **kwargs)
        return self._request(model=model, messages=messages, stream=False, **kwargs)

    def balance(self) -> dict:
        """
        Check remaining credits on the API key.

        Returns:
            dict: {"credits_remaining": ..., "credits_used": ...}
        """
        headers = self._auth_headers()
        try:
            resp = self._session.get(f"{self.base_url}/balance", headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def topup(self, amount_usd: float = 1.0) -> dict:
        """
        Fund the API key using x402 payment.
        Each $1.00 USD adds 100,000 credits.

        Args:
            amount_usd: Amount in USD to top up (default $1.00).

        Returns:
            dict: The gateway response (new balance).
        """
        if not _X402_AVAILABLE:
            return {"error": "x402 SDK not installed. Run 'pip install x402'"}
        if not self.wallet:
            return {"error": "No wallet (private key) configured for topup."}

        logger.info("Executing topup via x402 | amount=$%.2f", amount_usd)
        try:
            client = x402ClientSync()
            # Ensure RPC is set for the x402 SDK
            if not os.getenv("ETH_RPC_URL"):
                os.environ["ETH_RPC_URL"] = "https://sepolia.base.org"
            
            signer = EthAccountSigner(self.wallet.account)
            register_exact_evm_client(client, signer)
            session = x402_requests(client)

            # The gateway topup endpoint handles the x402 handshake
            resp = session.post(
                f"{self.base_url}/key/topup",
                json={"api_key": self.api_key},
                headers={"Content-Type": "application/json"},
                timeout=300 # Long timeout for on-chain TX
            )

            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            logger.error("Topup failed: %s", e)
            return {"error": str(e)}

    def models(self) -> list:
        """
        List available models.

        Returns:
            list: Model objects from /v1/models endpoint.
        """
        headers = self._auth_headers()
        try:
            resp = self._session.get(f"{self.base_url}/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", data)
            return []
        except Exception as e:
            logger.error("Failed to list models: %s", e)
            return []

    def budget_summary(self) -> dict:
        """Get today's spending summary."""
        summary = self._enforcer.tracker.summary()
        summary["policy"] = {
            "daily_budget": self.policy.daily_budget,
            "max_per_request": self.policy.max_spend_per_request,
            "remaining": round(self.policy.daily_budget - summary["spent_today_usd"], 4),
            "emergency_halt": self.policy.emergency_halt,
        }
        return summary

    def halt(self):
        """Emergency halt — stop all spending immediately."""
        self.policy.emergency_halt = True
        logger.warning("EMERGENCY HALT ACTIVATED — all spending is frozen")

    def resume(self):
        """Resume spending after an emergency halt."""
        self.policy.emergency_halt = False
        logger.info("Emergency halt deactivated — spending resumed")

    # ──────────────────────────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        """Build authentication headers."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, model: str, messages: list, stream: bool = False, **kwargs) -> dict:
        """
        Core request method with policy enforcement and auto-402 handling.
        """
        # --- Policy Check ---
        block_reason = self._enforcer.check_pre_request(model, estimated_cost_usd=0.001)
        if block_reason:
            logger.warning("Policy blocked request: %s", block_reason)
            return {"error": block_reason}

        # --- Build Payload ---
        payload = {"model": model, "messages": messages, "stream": stream}
        for k in ("max_tokens", "temperature", "tools", "tool_choice", "top_p", "stop"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        headers = self._auth_headers()

        # --- Send ---
        try:
            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=120,
            )
        except requests.exceptions.Timeout:
            return {"error": "Request timed out after 120s"}
        except Exception as e:
            return {"error": f"Connection error: {e}"}

        # --- 200 OK ---
        if resp.status_code == 200:
            data = resp.json()
            # Record estimated cost
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            est_cost = total_tokens * 0.000002  # Rough estimate: $2/1M tokens
            self._enforcer.record_spend(est_cost)
            logger.info("Chat OK | model=%s | tokens=%d | est_cost=$%.6f", model, total_tokens, est_cost)
            return data

        # --- 402 Payment Required → Auto-Pay ---
        if resp.status_code == 402:
            logger.info("402 received — attempting auto-payment via x402")
            return self._handle_402(payload, headers)

        # --- 401 Unauthorized ---
        if resp.status_code == 401:
            return {"error": "Unauthorized (401): Invalid API key", "detail": resp.text}

        # --- Other errors ---
        return {"error": f"HTTP {resp.status_code}", "detail": resp.text}

    def _request_stream(self, model: str, messages: list, **kwargs) -> Iterator[str]:
        """
        Streaming request — yields content chunks.
        """
        # --- Policy Check ---
        block_reason = self._enforcer.check_pre_request(model, estimated_cost_usd=0.001)
        if block_reason:
            logger.warning("Policy blocked stream: %s", block_reason)
            yield f"[POLICY BLOCKED] {block_reason}"
            return

        # --- Build Payload ---
        payload = {"model": model, "messages": messages, "stream": True}
        for k in ("max_tokens", "temperature", "tools", "tool_choice", "top_p", "stop"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        headers = self._auth_headers()

        try:
            resp = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=120,
                stream=True,
            )
        except Exception as e:
            yield f"[ERROR] {e}"
            return

        if resp.status_code != 200:
            yield f"[ERROR] HTTP {resp.status_code}: {resp.text[:200]}"
            return

        # --- Parse SSE stream ---
        total_chars = 0
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        total_chars += len(content)
                        yield content
                except json.JSONDecodeError:
                    continue

        # Rough cost estimate for streaming
        est_tokens = total_chars / 4  # ~4 chars per token
        est_cost = est_tokens * 0.000002
        self._enforcer.record_spend(est_cost)
        logger.info("Stream complete | model=%s | chars=%d | est_cost=$%.6f", model, total_chars, est_cost)

    def _handle_402(self, payload: dict, headers: dict) -> dict:
        """
        Handle 402 Payment Required by auto-signing via x402.
        """
        if not _X402_AVAILABLE:
            return {
                "error": "402 Payment Required but x402 SDK not installed",
                "fix": "pip install 'x402[requests]'",
            }

        if not self.wallet:
            return {
                "error": "402 Payment Required but no wallet configured",
                "fix": "Initialize with auto_wallet=True or provide private_key",
            }

        try:
            client = x402ClientSync()
            signer = EthAccountSigner(self.wallet.account)
            register_exact_evm_client(client, signer)
            session = x402_requests(client)

            resp = session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={**headers, "Content-Type": "application/json"},
                timeout=120,
            )

            if resp.ok:
                data = resp.json()
                # Record the x402 payment cost
                usage = data.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)
                est_cost = total_tokens * 0.000002
                self._enforcer.record_spend(est_cost)
                logger.info("x402 auto-pay successful | tokens=%d", total_tokens)
                return data
            else:
                return {"error": f"x402 payment failed: HTTP {resp.status_code}", "detail": resp.text}

        except Exception as e:
            logger.error("x402 auto-pay error: %s", e)
            return {"error": f"x402 payment error: {e}"}
