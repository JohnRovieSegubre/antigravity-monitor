"""
hand_history.py — Records each poker hand to a JSON Lines file.
Tracks cards, board, action taken, equity, EV, and stack deltas.
"""
import json
import os
import time
from datetime import datetime

DEFAULT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "session_history.jsonl"
)


class HandHistory:
    def __init__(self, log_path: str = DEFAULT_LOG_PATH):
        self.log_path = log_path
        self.hand_count = 0
        self._last_hero_cards = None  # For detecting new hands

        # Load existing hand count from file
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    self.hand_count = sum(1 for _ in f)
            except Exception:
                self.hand_count = 0

    def is_new_hand(self, hero_cards: list) -> bool:
        """Detect if the current cards represent a new hand."""
        if not hero_cards or len(hero_cards) < 2:
            return False

        card_key = (
            hero_cards[0].get("rank", "?") + hero_cards[0].get("suit", "?"),
            hero_cards[1].get("rank", "?") + hero_cards[1].get("suit", "?"),
        )

        if card_key == self._last_hero_cards:
            return False

        # Cards changed — new hand
        self._last_hero_cards = card_key
        return True

    def record_hand(
        self,
        client: str,
        hero_cards: list,
        board_cards: list,
        stage: str,
        pot: float,
        to_call: float,
        stack_before: float,
        stack_after: float,
        equity: float,
        action: str,
        ev_estimate: float,
        pot_odds: float = 0.0,
        spr: float = 0.0,
        hand_class: str = "",
    ) -> dict:
        """Record a single hand action to the JSONL log."""
        self.hand_count += 1

        # Build card strings
        hero_str = []
        for c in hero_cards:
            r = c.get("rank", "?")
            s = c.get("suit", "?")
            hero_str.append(f"{r}{s}")

        board_str = []
        for c in board_cards:
            r = c.get("rank", "?")
            s = c.get("suit", "?")
            board_str.append(f"{r}{s}")

        result_bb = round(stack_after - stack_before, 2) if stack_after > 0 else 0.0

        record = {
            "hand_id": self.hand_count,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "client": client,
            "hero_cards": hero_str,
            "board": board_str,
            "stage": stage,
            "hand_class": hand_class,
            "pot": round(pot, 2),
            "to_call": round(to_call, 2),
            "stack_before": round(stack_before, 2),
            "stack_after": round(stack_after, 2),
            "equity": round(equity, 1),
            "pot_odds": round(pot_odds, 1),
            "spr": round(spr, 1),
            "action": action,
            "ev_estimate": round(ev_estimate, 2),
            "result_bb": result_bb,
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[HandHistory] Error writing log: {e}")

        return record

    def get_last_n(self, n: int = 10) -> list:
        """Return the last N hand records."""
        if not os.path.exists(self.log_path):
            return []

        records = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception:
            return []

        return records[-n:]

    def get_all(self) -> list:
        """Return all hand records."""
        return self.get_last_n(n=999999)

    def get_session_summary(self) -> dict:
        """Calculate aggregate session statistics."""
        records = self.get_all()
        if not records:
            return {
                "total_hands": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "fold_pct": 0.0,
                "call_pct": 0.0,
                "raise_pct": 0.0,
                "avg_pot": 0.0,
                "biggest_win": 0.0,
                "biggest_loss": 0.0,
            }

        total = len(records)
        pnl = sum(r.get("result_bb", 0) for r in records)
        folds = sum(1 for r in records if r.get("action") == "FOLD")
        calls = sum(1 for r in records if r.get("action") == "CALL")
        raises = sum(1 for r in records if r.get("action") == "RAISE")
        results = [r.get("result_bb", 0) for r in records]

        return {
            "total_hands": total,
            "total_pnl": round(pnl, 2),
            "win_rate": round(pnl / total, 2) if total > 0 else 0.0,
            "fold_pct": round(folds / total * 100, 1) if total > 0 else 0.0,
            "call_pct": round(calls / total * 100, 1) if total > 0 else 0.0,
            "raise_pct": round(raises / total * 100, 1) if total > 0 else 0.0,
            "avg_pot": round(sum(r.get("pot", 0) for r in records) / total, 1),
            "biggest_win": round(max(results), 2) if results else 0.0,
            "biggest_loss": round(min(results), 2) if results else 0.0,
        }

    def clear_session(self):
        """Clear the session history (start fresh)."""
        self.hand_count = 0
        self._last_hero_cards = None
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
