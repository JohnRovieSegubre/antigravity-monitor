"""
strategy.py — Advanced poker decision engine for Phase 3.
Combines equity, pot odds, stack-to-pot ratio (SPR), and hand strength
to produce action recommendations with EV estimates.
"""


# ─── Preflop hand tiers ───────────────────────────────────────────────
# Groups hands into tiers for preflop decision adjustments.
PREMIUM_HANDS = {"AA", "KK", "QQ", "JJ", "AKs", "AKo"}
STRONG_HANDS  = {"TT", "99", "AQs", "AQo", "AJs", "KQs"}
PLAYABLE_HANDS = {
    "88", "77", "66", "ATs", "ATo", "AJs", "KJs", "KQo",
    "QJs", "JTs", "T9s", "98s", "87s", "76s",
}


def _hand_tier(hand_class: str) -> str:
    """Classify a preflop hand description into a tier."""
    if not hand_class:
        return "weak"

    # Normalize — our equity.py returns e.g. "AK Suited" or "Pocket Qs"
    hc = hand_class.strip()

    # Pocket pairs
    if hc.startswith("Pocket"):
        rank = hc.replace("Pocket ", "").replace("s", "")
        pair_key = rank[0] * 2  # "A" -> "AA"
        if pair_key in PREMIUM_HANDS:
            return "premium"
        if pair_key in STRONG_HANDS:
            return "strong"
        if pair_key in PLAYABLE_HANDS:
            return "playable"
        return "marginal"

    # Non-pair hands like "AK Suited", "Q7 Offsuit"
    parts = hc.split()
    if len(parts) >= 2:
        ranks = parts[0]  # e.g. "AK", "Q7"
        suited_str = parts[1] if len(parts) > 1 else ""
        suffix = "s" if suited_str.lower() == "suited" else "o"
        key_s = ranks + "s"
        key_o = ranks + "o"
        key = key_s if suffix == "s" else key_o

        if key in PREMIUM_HANDS or key_s in PREMIUM_HANDS:
            return "premium"
        if key in STRONG_HANDS or key_s in STRONG_HANDS:
            return "strong"
        if key in PLAYABLE_HANDS or key_s in PLAYABLE_HANDS:
            return "playable"

    return "weak"


def decide(equity: float, pot: float, to_call: float, stack: float,
           stage: str, hand_class: str) -> dict:
    """
    Produce a poker decision combining multiple factors.

    Returns:
        dict with keys:
            action:       "FOLD" | "CALL" | "RAISE"
            ev_estimate:  float — estimated expected value in BB
            pot_odds:     float — pot odds as a percentage
            spr:          float — stack-to-pot ratio
            reasoning:    str   — human-readable explanation
    """
    # ── Guard: no cards yet ──
    if equity <= 0:
        return {
            "action": "WAITING",
            "ev_estimate": 0.0,
            "pot_odds": 0.0,
            "spr": 0.0,
            "reasoning": "Waiting for cards to be dealt...",
        }

    # ── Core calculations ──
    pot_odds = (to_call / (pot + to_call) * 100) if (pot + to_call) > 0 else 0
    ev = (equity / 100 * (pot + to_call)) - ((1 - equity / 100) * to_call)
    spr = stack / pot if pot > 0 else 999.0

    tier = _hand_tier(hand_class) if stage == "Preflop" else ""

    # ── Decision matrix ──
    action = "FOLD"
    reason_parts = []

    if stage == "Preflop":
        action, reason_parts = _decide_preflop(
            equity, pot_odds, ev, spr, tier, to_call, stack, hand_class
        )
    else:
        action, reason_parts = _decide_postflop(
            equity, pot_odds, ev, spr, to_call, stack, stage, hand_class
        )

    reasoning = f"{stage}: " + " ".join(reason_parts)

    return {
        "action": action,
        "ev_estimate": round(ev, 2),
        "pot_odds": round(pot_odds, 1),
        "spr": round(spr, 1),
        "reasoning": reasoning,
    }


# ─── Preflop logic ───────────────────────────────────────────────────

def _decide_preflop(equity, pot_odds, ev, spr, tier, to_call, stack, hand_class):
    reasons = []

    if tier == "premium":
        reasons.append(f"Premium hand ({hand_class}) — always raise for value.")
        reasons.append(f"Equity {equity:.0f}% vs pot odds {pot_odds:.0f}%.")
        return "RAISE", reasons

    if tier == "strong":
        if to_call <= 0:
            reasons.append(f"Strong hand ({hand_class}), no bet to call — raise for value.")
            return "RAISE", reasons
        if equity > pot_odds + 5:
            reasons.append(f"Strong hand ({hand_class}), equity {equity:.0f}% beats pot odds {pot_odds:.0f}%.")
            reasons.append(f"EV = {ev:+.1f} BB. Raise.")
            return "RAISE", reasons
        reasons.append(f"Strong hand ({hand_class}) but tight spot. Equity {equity:.0f}% ≈ pot odds {pot_odds:.0f}%. Call.")
        return "CALL", reasons

    if tier == "playable":
        if to_call <= 0:
            reasons.append(f"Playable hand ({hand_class}), no bet to call — raise light.")
            return "RAISE", reasons
        if equity > pot_odds + 3:
            reasons.append(f"Playable hand ({hand_class}), equity {equity:.0f}% > pot odds {pot_odds:.0f}%. EV = {ev:+.1f} BB. Call.")
            return "CALL", reasons
        reasons.append(f"Playable hand ({hand_class}) but equity {equity:.0f}% doesn't cover pot odds {pot_odds:.0f}%. Fold.")
        return "FOLD", reasons

    if tier == "marginal":
        if to_call <= 0:
            reasons.append(f"Marginal hand ({hand_class}), free play — call/check.")
            return "CALL", reasons
        if equity > pot_odds + 8:
            reasons.append(f"Marginal hand ({hand_class}), equity {equity:.0f}% covers pot odds {pot_odds:.0f}% with margin. Call.")
            return "CALL", reasons
        reasons.append(f"Marginal hand ({hand_class}), equity {equity:.0f}% doesn't justify calling {pot_odds:.0f}% pot odds. Fold.")
        return "FOLD", reasons

    # Weak / unknown
    if to_call <= 0:
        reasons.append(f"Weak hand ({hand_class}), but free to see a flop. Check.")
        return "CALL", reasons
    reasons.append(f"Weak hand ({hand_class}) with {equity:.0f}% equity. Not worth calling. Fold.")
    return "FOLD", reasons


# ─── Post-flop logic ─────────────────────────────────────────────────

def _decide_postflop(equity, pot_odds, ev, spr, to_call, stack, stage, hand_class):
    reasons = []

    # Low SPR = pot-committed territory
    if spr < 2 and equity > 35:
        reasons.append(f"Low SPR ({spr:.1f}) — effectively pot-committed.")
        reasons.append(f"Equity {equity:.0f}% is enough to shove/call. Push!")
        return "RAISE", reasons

    # Strong equity advantage
    if equity > 65:
        reasons.append(f"Dominant hand ({hand_class}) with {equity:.0f}% equity.")
        reasons.append(f"EV = {ev:+.1f} BB (pot odds {pot_odds:.0f}%). Raise for value.")
        return "RAISE", reasons

    # Positive EV call
    if equity > pot_odds and ev > 0:
        if equity > 55:
            reasons.append(f"Good hand ({hand_class}), equity {equity:.0f}% > pot odds {pot_odds:.0f}%.")
            reasons.append(f"EV = {ev:+.1f} BB. Raise for thin value.")
            return "RAISE", reasons
        reasons.append(f"Your hand ({hand_class}) has {equity:.0f}% equity vs {pot_odds:.0f}% pot odds.")
        reasons.append(f"EV = {ev:+.1f} BB — profitable to call.")
        return "CALL", reasons

    # Marginal / drawing
    if equity > pot_odds - 5 and to_call < stack * 0.1:
        reasons.append(f"Borderline spot ({hand_class}): equity {equity:.0f}% ≈ pot odds {pot_odds:.0f}%.")
        reasons.append(f"Small call relative to stack. Worth taking the risk. Call.")
        return "CALL", reasons

    # Default fold
    reasons.append(f"Your hand ({hand_class}) has only {equity:.0f}% equity vs {pot_odds:.0f}% pot odds needed.")
    reasons.append(f"EV = {ev:+.1f} BB — negative expectation. Fold and wait.")
    return "FOLD", reasons
