"""
equity.py — Real-time poker equity calculator using Monte Carlo simulation.
Uses the `treys` library for hand evaluation.
"""
from treys import Card, Evaluator, Deck
import random

evaluator = Evaluator()

# Maps our vision symbols to treys format
RANK_MAP = {
    'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T',
    '9': '9', '8': '8', '7': '7', '6': '6', '5': '5',
    '4': '4', '3': '3', '2': '2'
}

SUIT_MAP = {
    '♥': 'h', '♦': 'd', '♣': 'c', '♠': 's'
}


def vision_to_treys(rank, suit):
    """Convert vision-detected rank/suit into a treys Card integer."""
    r = RANK_MAP.get(rank)
    s = SUIT_MAP.get(suit)
    if r is None or s is None:
        return None
    try:
        return Card.new(r + s)
    except Exception:
        return None


def calculate_equity(hero_cards, board_cards, num_opponents=2, simulations=1000):
    """
    Calculate hero's equity via Monte Carlo simulation.

    Args:
        hero_cards: list of dicts [{"rank": "A", "suit": "♠"}, ...]
        board_cards: list of dicts [{"rank": "K", "suit": "♥"}, ...]
        num_opponents: number of opponents to simulate (default 2)
        simulations: number of Monte Carlo iterations (default 1000)

    Returns:
        dict with:
            - equity: float (0-100, percentage)
            - hand_class: str (e.g. "Two Pair", "Flush", etc.)
            - stage: str ("Preflop", "Flop", "Turn", "River")
    """
    # Convert hero cards
    hero = []
    for c in hero_cards:
        card = vision_to_treys(c.get('rank', '?'), c.get('suit', '?'))
        if card is None:
            return {"equity": 0, "hand_class": "Unknown", "stage": "Waiting"}
        hero.append(card)

    if len(hero) != 2:
        return {"equity": 0, "hand_class": "Unknown", "stage": "Waiting"}

    # Convert board cards
    board = []
    for c in board_cards:
        card = vision_to_treys(c.get('rank', '?'), c.get('suit', '?'))
        if card is not None:
            board.append(card)

    # Determine stage
    if len(board) == 0:
        stage = "Preflop"
    elif len(board) == 3:
        stage = "Flop"
    elif len(board) == 4:
        stage = "Turn"
    elif len(board) == 5:
        stage = "River"
    else:
        stage = "Unknown"

    # Known cards that can't appear in the simulation
    dead_cards = set(hero + board)

    # Build the remaining deck
    full_deck = Deck.GetFullDeck()
    remaining = [c for c in full_deck if c not in dead_cards]

    wins = 0
    ties = 0
    total = 0

    for _ in range(simulations):
        random.shuffle(remaining)
        idx = 0

        # Deal remaining community cards
        cards_needed = 5 - len(board)
        sim_board = board + remaining[idx:idx + cards_needed]
        idx += cards_needed

        # Deal opponent hands
        opponent_hands = []
        valid_sim = True
        for _ in range(num_opponents):
            if idx + 2 > len(remaining):
                valid_sim = False
                break
            opponent_hands.append(remaining[idx:idx + 2])
            idx += 2

        if not valid_sim:
            continue

        # Evaluate hero
        hero_score = evaluator.evaluate(sim_board, hero)

        # Evaluate all opponents
        best_opp_score = 9999  # Lower is better in treys
        for opp_hand in opponent_hands:
            opp_score = evaluator.evaluate(sim_board, opp_hand)
            if opp_score < best_opp_score:
                best_opp_score = opp_score

        if hero_score < best_opp_score:
            wins += 1
        elif hero_score == best_opp_score:
            ties += 1

        total += 1

    if total == 0:
        equity_pct = 0
    else:
        equity_pct = round(((wins + ties * 0.5) / total) * 100, 1)

    # Get hand class for current board state
    if len(board) >= 3:
        hero_class = evaluator.get_rank_class(evaluator.evaluate(board, hero))
        hand_class = evaluator.class_to_string(hero_class)
    else:
        # Preflop: describe the hand
        hand_class = _describe_preflop(hero_cards)

    return {
        "equity": equity_pct,
        "hand_class": hand_class,
        "stage": stage
    }


def _describe_preflop(hero_cards):
    """Generate a human-readable preflop hand description."""
    r1 = hero_cards[0].get('rank', '?')
    r2 = hero_cards[1].get('rank', '?')
    s1 = hero_cards[0].get('suit', '?')
    s2 = hero_cards[1].get('suit', '?')

    if r1 == r2:
        return f"Pocket {r1}s"

    suited = "Suited" if s1 == s2 else "Offsuit"
    # Order by rank strength
    rank_order = "AKQJT98765432"
    if rank_order.index(r1) > rank_order.index(r2):
        r1, r2 = r2, r1

    return f"{r1}{r2} {suited}"
