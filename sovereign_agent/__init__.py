"""
Sovereign Agent SDK
====================
The reference agent runtime for Sovereign API.

Install:
    pip install sovereign-agent

Usage:
    from sovereign_agent import SovereignAgent

    agent = SovereignAgent()
    response = agent.chat("Hello!")
"""

from .client import SovereignAgent
from .wallet import SovereignWallet
from .policy import SpendPolicy, BudgetTracker, PolicyEnforcer

__version__ = "1.0.0"
__all__ = [
    "SovereignAgent",
    "SovereignWallet",
    "SpendPolicy",
    "BudgetTracker",
    "PolicyEnforcer",
]
