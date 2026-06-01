import os
import time
import json
from flask import Flask, send_from_directory, Response, jsonify
from vision import PokerVision
from hand_history import HandHistory
from session_tracker import SessionTracker

app = Flask(__name__, static_folder='static')
vision_engine = PokerVision()
hand_history = HandHistory()
session = SessionTracker()

# Track previous state for hand boundary detection
_prev_stack = 0.0
_prev_cards = None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/history')
def api_history():
    """Full hand history as JSON."""
    return jsonify(hand_history.get_all())

@app.route('/api/session')
def api_session():
    """Current session stats as JSON."""
    return jsonify(session.to_dict())

@app.route('/api/clear')
def api_clear():
    """Clear session and history (new session)."""
    global _prev_stack, _prev_cards
    hand_history.clear_session()
    session.__init__()
    _prev_stack = 0.0
    _prev_cards = None
    return jsonify({"status": "cleared"})

@app.route('/stream')
def stream():
    def generate_data():
        global _prev_stack, _prev_cards

        while True:
            state = vision_engine.parse_state()

            if "error" in state:
                payload = {
                    "hero_cards": [{"rank": "?", "suit": "", "color": "black"}, {"rank": "?", "suit": "", "color": "black"}],
                    "board_cards": [],
                    "equity": 0,
                    "action": "WAITING...",
                    "pot": "0 BB",
                    "stack": "0 BB",
                    "to_call": "0 BB",
                    "ev_estimate": 0,
                    "pot_odds": 0,
                    "spr": 0,
                    "reasoning": "Waiting for poker table...",
                    "hand_class": "",
                    "stage": "",
                    "session_stats": session.to_dict(),
                    "last_hands": hand_history.get_last_n(10),
                }
            else:
                # Color code cards for frontend
                for card in state['hero_cards']:
                    card['color'] = 'red' if card['suit'] in ['♥', '♦'] else 'black'
                for card in state.get('board_cards', []):
                    card['color'] = 'red' if card['suit'] in ['♥', '♦'] else 'black'

                # Track hand boundaries via card changes
                current_stack = state.get('stack', 0)
                current_cards = (
                    state['hero_cards'][0].get('rank', '?') + state['hero_cards'][0].get('suit', '?'),
                    state['hero_cards'][1].get('rank', '?') + state['hero_cards'][1].get('suit', '?'),
                )

                # Set initial stack
                session.set_initial_stack(current_stack)

                # Detect new hand and record the previous one
                action = state.get('action', 'WAITING')
                if _prev_cards and current_cards != _prev_cards and action != 'WAITING':
                    # New cards dealt — previous hand ended
                    # Record the action that was taken
                    session.record_action(
                        action=action,
                        ev_estimate=state.get('ev_estimate', 0),
                        stack_before=_prev_stack if _prev_stack > 0 else current_stack,
                        stack_after=current_stack,
                        pot=state.get('pot', 0),
                    )
                    hand_history.record_hand(
                        client=state.get('client', ''),
                        hero_cards=state['hero_cards'],
                        board_cards=state.get('board_cards', []),
                        stage=state.get('stage', ''),
                        pot=state.get('pot', 0),
                        to_call=state.get('to_call', 0),
                        stack_before=_prev_stack if _prev_stack > 0 else current_stack,
                        stack_after=current_stack,
                        equity=state.get('equity', 0),
                        action=action,
                        ev_estimate=state.get('ev_estimate', 0),
                        pot_odds=state.get('pot_odds', 0),
                        spr=state.get('spr', 0),
                        hand_class=state.get('hand_class', ''),
                    )

                _prev_cards = current_cards
                _prev_stack = current_stack

                payload = {
                    "hero_cards": state['hero_cards'],
                    "board_cards": state.get('board_cards', []),
                    "equity": state.get('equity', 0),
                    "action": action,
                    "pot": f"{state.get('pot', 0)} BB",
                    "stack": f"{state.get('stack', 0)} BB",
                    "to_call": f"{state.get('to_call', 0)} BB",
                    "ev_estimate": state.get('ev_estimate', 0),
                    "pot_odds": state.get('pot_odds', 0),
                    "spr": state.get('spr', 0),
                    "reasoning": state.get('reasoning', ''),
                    "hand_class": state.get('hand_class', ''),
                    "stage": state.get('stage', ''),
                    "client": state.get('client', ''),
                    "session_stats": session.to_dict(),
                    "last_hands": hand_history.get_last_n(10),
                }

            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(1)

    return Response(generate_data(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Starting LIVE Poker Advisor Dashboard (Phase 3 — EV Tracker)...")
    app.run(host='0.0.0.0', port=8888, threaded=True)
