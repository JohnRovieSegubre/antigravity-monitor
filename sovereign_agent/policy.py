"""
Sovereign Agent — Policy Enforcement
======================================
Mechanical safety layer for agent spending.
Enforced in code, not in prompts.

Features:
- Per-request spend cap
- Daily budget limit
- Model allowlist
- Emergency halt (kill switch)
- Persistent budget tracking via ~/.sovereign/budget.json
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("sovereign_agent.policy")

BUDGET_FILE = Path.home() / ".sovereign" / "budget.json"


@dataclass
class SpendPolicy:
    """
    Policy configuration for agent spending limits.
    
    Usage:
        policy = SpendPolicy(
            max_spend_per_request=0.05,  # $0.05 max per request
            daily_budget=5.00,           # $5.00 per day
            allowed_models=["sovereign/deepseek-r1", "sovereign/llama-4-maverick"],
            emergency_halt=False,
        )
    """
    max_spend_per_request: float = 0.05   # USD
    daily_budget: float = 5.00            # USD
    allowed_models: list = field(default_factory=list)  # Empty = all allowed
    emergency_halt: bool = False


class BudgetTracker:
    """
    Tracks cumulative spend per day. Persisted to ~/.sovereign/budget.json.
    Resets daily automatically.
    """

    def __init__(self, budget_path: str = None):
        self._path = Path(budget_path) if budget_path else BUDGET_FILE
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                pass
        return {"date": self._today(), "total_usd": 0.0, "requests": 0}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    @staticmethod
    def _today() -> str:
        return time.strftime("%Y-%m-%d")

    def _reset_if_new_day(self):
        if self._data.get("date") != self._today():
            logger.info("New day detected, resetting budget tracker")
            self._data = {"date": self._today(), "total_usd": 0.0, "requests": 0}
            self._save()

    @property
    def spent_today(self) -> float:
        self._reset_if_new_day()
        return self._data.get("total_usd", 0.0)

    @property
    def requests_today(self) -> int:
        self._reset_if_new_day()
        return self._data.get("requests", 0)

    def record_spend(self, amount_usd: float):
        """Record a spend event."""
        self._reset_if_new_day()
        self._data["total_usd"] = round(self._data.get("total_usd", 0.0) + amount_usd, 6)
        self._data["requests"] = self._data.get("requests", 0) + 1
        self._save()
        logger.info("Recorded spend: $%.4f | Daily total: $%.4f | Requests: %d",
                     amount_usd, self._data["total_usd"], self._data["requests"])

    def summary(self) -> dict:
        self._reset_if_new_day()
        return {
            "date": self._data["date"],
            "spent_today_usd": self._data["total_usd"],
            "requests_today": self._data["requests"],
        }


class PolicyEnforcer:
    """
    Validates requests against the spend policy before execution.
    """

    def __init__(self, policy: SpendPolicy, tracker: BudgetTracker = None):
        self.policy = policy
        self.tracker = tracker or BudgetTracker()

    def check_pre_request(self, model: str, estimated_cost_usd: float = 0.0) -> Optional[str]:
        """
        Validate a request BEFORE sending it.
        Returns None if OK, or an error message string if blocked.
        """
        if self.policy.emergency_halt:
            return "BLOCKED: Emergency halt is active. All spending is frozen."

        if self.policy.allowed_models and model not in self.policy.allowed_models:
            return f"BLOCKED: Model '{model}' is not in the allowed list: {self.policy.allowed_models}"

        if estimated_cost_usd > self.policy.max_spend_per_request:
            return (f"BLOCKED: Estimated cost ${estimated_cost_usd:.4f} exceeds "
                    f"per-request cap ${self.policy.max_spend_per_request:.4f}")

        remaining = self.policy.daily_budget - self.tracker.spent_today
        if remaining <= 0:
            return (f"BLOCKED: Daily budget exhausted. "
                    f"Spent: ${self.tracker.spent_today:.4f} / ${self.policy.daily_budget:.4f}")

        return None  # All clear

    def record_spend(self, amount_usd: float):
        """Record that a request was completed and money was spent."""
        self.tracker.record_spend(amount_usd)
