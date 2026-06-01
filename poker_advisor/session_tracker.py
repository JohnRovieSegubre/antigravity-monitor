"""
session_tracker.py — Real-time session statistics engine for Phase 3.
Tracks running P&L, EV curve, VPIP, and per-hand metrics for the dashboard.
"""
from datetime import datetime


class SessionTracker:
    def __init__(self):
        self.start_time = datetime.now().isoformat(timespec="seconds")
        self.hands_played = 0
        self.initial_stack = None
        self.current_stack = 0.0

        # Running totals
        self.total_pnl = 0.0
        self.total_ev = 0.0
        self.folds = 0
        self.calls = 0
        self.raises = 0

        # Per-hand EV history for graphing
        self.ev_history = []        # [{hand_id, cumulative_ev, pnl, action}]
        self.pnl_history = []       # [{hand_id, cumulative_pnl}]

        # Extremes
        self.biggest_win = 0.0
        self.biggest_loss = 0.0
        self.current_streak = 0     # positive = winning, negative = losing
        self.best_streak = 0
        self.worst_streak = 0

    def set_initial_stack(self, stack: float):
        """Set the starting stack for the session."""
        if self.initial_stack is None and stack > 0:
            self.initial_stack = stack
            self.current_stack = stack

    def record_action(self, action: str, ev_estimate: float,
                      stack_before: float, stack_after: float,
                      pot: float = 0.0):
        """Record a hand action and update all running stats."""
        self.hands_played += 1

        # Track action distribution
        if action == "FOLD":
            self.folds += 1
        elif action == "CALL":
            self.calls += 1
        elif action == "RAISE":
            self.raises += 1

        # Stack delta = actual result
        result = round(stack_after - stack_before, 2) if stack_after > 0 else 0.0
        self.total_pnl += result
        self.total_ev += ev_estimate
        self.current_stack = stack_after

        # Update extremes
        if result > self.biggest_win:
            self.biggest_win = result
        if result < self.biggest_loss:
            self.biggest_loss = result

        # Update streak
        if result > 0:
            self.current_streak = max(1, self.current_streak + 1)
        elif result < 0:
            self.current_streak = min(-1, self.current_streak - 1)
        # result == 0 keeps streak unchanged (fold)

        self.best_streak = max(self.best_streak, self.current_streak)
        self.worst_streak = min(self.worst_streak, self.current_streak)

        # Append to history for EV graph
        self.ev_history.append({
            "hand_id": self.hands_played,
            "cumulative_ev": round(self.total_ev, 2),
            "action": action,
        })
        self.pnl_history.append({
            "hand_id": self.hands_played,
            "cumulative_pnl": round(self.total_pnl, 2),
        })

    def vpip_pct(self) -> float:
        """VPIP = Voluntarily Put $ In Pot = (calls + raises) / total hands."""
        if self.hands_played == 0:
            return 0.0
        return round((self.calls + self.raises) / self.hands_played * 100, 1)

    def win_rate(self) -> float:
        """Win rate in BB/hand."""
        if self.hands_played == 0:
            return 0.0
        return round(self.total_pnl / self.hands_played, 2)

    def to_dict(self) -> dict:
        """Export full session state for dashboard consumption."""
        return {
            "start_time": self.start_time,
            "hands_played": self.hands_played,
            "initial_stack": self.initial_stack or 0.0,
            "current_stack": round(self.current_stack, 2),
            "total_pnl": round(self.total_pnl, 2),
            "total_ev": round(self.total_ev, 2),
            "win_rate": self.win_rate(),
            "vpip": self.vpip_pct(),
            "fold_pct": round(self.folds / self.hands_played * 100, 1) if self.hands_played else 0.0,
            "call_pct": round(self.calls / self.hands_played * 100, 1) if self.hands_played else 0.0,
            "raise_pct": round(self.raises / self.hands_played * 100, 1) if self.hands_played else 0.0,
            "biggest_win": round(self.biggest_win, 2),
            "biggest_loss": round(self.biggest_loss, 2),
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "worst_streak": self.worst_streak,
            "ev_history": self.ev_history[-50:],   # Last 50 for the graph
            "pnl_history": self.pnl_history[-50:],
        }
