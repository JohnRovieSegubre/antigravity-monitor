"""
Sovereign Agent — Wallet Manager
=================================
Auto-generates and persists an EVM wallet for autonomous agent use.

On first run: creates a new private key at ~/.sovereign/wallet.json
On subsequent runs: loads the existing wallet.
"""

import json
import os
import logging
from pathlib import Path

from eth_account import Account

logger = logging.getLogger("sovereign_agent.wallet")

SOVEREIGN_DIR = Path.home() / ".sovereign"
WALLET_FILE = SOVEREIGN_DIR / "wallet.json"
CONFIG_FILE = SOVEREIGN_DIR / "config.json"


class SovereignWallet:
    """
    Auto-managed EVM wallet for Sovereign agents.
    
    Usage:
        wallet = SovereignWallet()
        print(wallet.address)  # 0x...
    """

    def __init__(self, wallet_path: str = None, private_key: str = None):
        self._wallet_path = Path(wallet_path) if wallet_path else WALLET_FILE

        if private_key:
            # Explicit key provided — use it, don't persist
            self._account = Account.from_key(private_key)
            self._private_key = private_key
            logger.info("Wallet loaded from explicit private key: %s", self.address)
        elif self._wallet_path.exists():
            self._load()
        else:
            self._generate()

    def _generate(self):
        """Generate a new EVM wallet and persist it."""
        self._wallet_path.parent.mkdir(parents=True, exist_ok=True)

        self._account = Account.create()
        self._private_key = self._account.key.hex()

        wallet_data = {
            "address": self._account.address,
            "private_key": self._private_key,
        }

        with open(self._wallet_path, "w") as f:
            json.dump(wallet_data, f, indent=2)

        # Restrict permissions (Unix only; no-op on Windows)
        try:
            os.chmod(self._wallet_path, 0o600)
        except (OSError, AttributeError):
            pass

        logger.info("New wallet generated: %s → %s", self.address, self._wallet_path)

    def _load(self):
        """Load existing wallet from disk."""
        with open(self._wallet_path, "r") as f:
            data = json.load(f)

        self._private_key = data["private_key"]
        self._account = Account.from_key(self._private_key)
        logger.info("Wallet loaded: %s ← %s", self.address, self._wallet_path)

    @property
    def address(self) -> str:
        return self._account.address

    @property
    def private_key(self) -> str:
        return self._private_key

    @property
    def account(self):
        return self._account

    def export(self) -> dict:
        """Export wallet info (address only — never expose private key in logs)."""
        return {"address": self.address, "wallet_path": str(self._wallet_path)}


def load_config() -> dict:
    """Load agent config from ~/.sovereign/config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save agent config to ~/.sovereign/config.json."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    logger.info("Config saved to %s", CONFIG_FILE)
