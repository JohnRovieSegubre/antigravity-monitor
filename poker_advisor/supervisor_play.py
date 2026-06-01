import time
import win32gui
import win32api
import win32con
import sys
import random
import os
import re

sys.path.append(r"C:\Users\rovie segubre\agent\poker_advisor")
from vision import PokerVision
from strategy import decide
from hand_history import HandHistory
from session_tracker import SessionTracker

LOG_FILE = r"C:\Users\rovie segubre\agent\poker_advisor\playtest_log.txt"

def log_event(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def human_click(x, y):
    x += random.randint(-5, 5)
    y += random.randint(-5, 5)
    win32api.SetCursorPos((x, y))
    time.sleep(random.uniform(0.2, 0.4))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(random.uniform(0.08, 0.15))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

def is_our_turn(v, img, client_type):
    h, w = img.shape[:2]
    try:
        if client_type == "888":
            crop = img[int(h*0.9):int(h*0.98), int(w*0.7):int(w*0.99)]
            text = v.reader.readtext(crop, detail=0)
            text_str = " ".join(text).lower()
            return any(x in text_str for x in ["bb", "to", "raise"]) or any(char.isdigit() for char in text_str)
        elif client_type == "CoinPoker":
            crop = img[int(h*0.88):int(h*0.97), int(w*0.5):int(w*0.98)]
            text = v.reader.readtext(crop, detail=0)
            text_str = " ".join(text).lower()
            return any(x in text_str for x in ["fold", "call", "check", "raise", "bet"])
    except Exception as e:
        log_event(f"Error in is_our_turn: {e}")
    return False

def get_button_coords(hwnd, client, action):
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bot - top
    
    if client == '888':
        if action == 'FOLD':
            return left + int(w * 0.76), top + int(h * 0.95)
        elif action == 'CALL':
            return left + int(w * 0.85), top + int(h * 0.95)
        elif action == 'RAISE':
            return left + int(w * 0.94), top + int(h * 0.95)
    else: # CoinPoker
        if action == 'FOLD':
            return left + int(w * 0.55), top + int(h * 0.92)
        elif action == 'CALL':
            return left + int(w * 0.75), top + int(h * 0.92)
        elif action == 'RAISE':
            return left + int(w * 0.90), top + int(h * 0.92)
    return None

def main():
    log_event("=== STARTING ANTIGRAVITY PHASE 3 PLAYTEST (EV TRACKER) ===")
    v = PokerVision()
    history = HandHistory()
    session = SessionTracker()
    
    initial_stack = None
    last_state_str = ""
    last_status_print = 0
    prev_stack = 0.0
    
    while True:
        try:
            hwnd, client = v.find_active_window()
            if not hwnd:
                if time.time() - last_status_print > 15:
                    log_event("Waiting for poker window...")
                    last_status_print = time.time()
                time.sleep(2)
                continue
                
            # Parse state (now includes strategy engine output)
            state = v.parse_state()
            if "error" in state:
                if time.time() - last_status_print > 15:
                    log_event(f"[{client}] Waiting for cards/action (Error: {state.get('error')})...")
                    last_status_print = time.time()
                time.sleep(2)
                continue
                
            img = v.client.capture_screen() if v.client else None
            if img is None:
                time.sleep(2)
                continue
                
            if state.get("action") == "WAITING":
                if time.time() - last_status_print > 15:
                    log_event(f"[{client}] Waiting for cards/action...")
                    last_status_print = time.time()
                time.sleep(2)
                continue
                
            # Check if it is our turn to act
            if not is_our_turn(v, img, client):
                if time.time() - last_status_print > 10:
                    log_event(f"[{client}] Cards dealt: {state.get('hand_class')}, but waiting for our turn...")
                    last_status_print = time.time()
                time.sleep(1.5)
                continue
                
            # It IS our turn!
            stack = state.get("stack", 0)
            if initial_stack is None and stack > 0:
                initial_stack = stack
                session.set_initial_stack(stack)
                log_event(f"Set initial stack size to {initial_stack} BB")
                
            # Check if stack is busted or tripled
            if stack <= 0.1 and initial_stack is not None:
                log_event("!!! STACK BUSTED !!! Stopping playtest loop.")
                log_event(f"=== SESSION SUMMARY: {session.hands_played} hands | P&L: {session.total_pnl:+.1f} BB | EV: {session.total_ev:+.1f} BB ===")
                break
            if initial_stack is not None and stack >= initial_stack * 3.0:
                log_event(f"!!! STACK TRIPLED !!! Started with {initial_stack} BB, now have {stack} BB. Stopping playtest loop.")
                log_event(f"=== SESSION SUMMARY: {session.hands_played} hands | P&L: {session.total_pnl:+.1f} BB | EV: {session.total_ev:+.1f} BB ===")
                break
                
            action = state.get("action", "FOLD")
            equity = state.get("equity", 0)
            hand_class = state.get("hand_class", "Unknown")
            pot = state.get("pot", 0)
            to_call = state.get("to_call", 0)
            ev_est = state.get("ev_estimate", 0)
            pot_odds = state.get("pot_odds", 0)
            spr = state.get("spr", 0)
            reasoning = state.get("reasoning", "")
            board = ", ".join([f"{c.get('rank','?')}{c.get('suit','?')}" for c in state.get("board_cards", [])])
            
            # Prevent double acting on identical state
            state_str = f"{hand_class}_{board}_{pot}_{stack}"
            if state_str == last_state_str:
                time.sleep(1)
                continue

            # Log the full strategy analysis
            log_event(f"YOUR TURN! Hand: {hand_class} | Board: [{board}] | Pot: {pot} BB | Stack: {stack} BB")
            log_event(f"  Strategy: Equity={equity}% | PotOdds={pot_odds}% | SPR={spr} | EV={ev_est:+.2f} BB")
            log_event(f"  Decision: {action} | {reasoning}")

            # Record to session tracker
            session.record_action(
                action=action,
                ev_estimate=ev_est,
                stack_before=prev_stack if prev_stack > 0 else stack,
                stack_after=stack,
                pot=pot,
            )

            # Record to hand history
            history.record_hand(
                client=client,
                hero_cards=state.get("hero_cards", []),
                board_cards=state.get("board_cards", []),
                stage=state.get("stage", ""),
                pot=pot,
                to_call=to_call,
                stack_before=prev_stack if prev_stack > 0 else stack,
                stack_after=stack,
                equity=equity,
                action=action,
                ev_estimate=ev_est,
                pot_odds=pot_odds,
                spr=spr,
                hand_class=hand_class,
            )
            
            # Execute the click
            coords = get_button_coords(hwnd, client, action)
            if coords:
                x, y = coords
                delay = random.uniform(1.5, 3.5)
                log_event(f"  Executing {action} at ({x}, {y}) after {delay:.2f}s pause...")
                time.sleep(delay)
                human_click(x, y)
                last_state_str = state_str
                prev_stack = stack
                time.sleep(5) # Wait for action to process
            else:
                log_event(f"Error: Could not determine button coordinates for action {action}")
                time.sleep(2)
                
        except Exception as e:
            log_event(f"Loop error: {e}")
            time.sleep(2)

    # Print final summary
    log_event("=== FINAL SESSION STATS ===")
    stats = session.to_dict()
    log_event(f"  Hands Played: {stats['hands_played']}")
    log_event(f"  Total P&L: {stats['total_pnl']:+.1f} BB")
    log_event(f"  Total EV: {stats['total_ev']:+.1f} BB")
    log_event(f"  Win Rate: {stats['win_rate']:+.2f} BB/hand")
    log_event(f"  VPIP: {stats['vpip']}%")
    log_event(f"  Fold/Call/Raise: {stats['fold_pct']}% / {stats['call_pct']}% / {stats['raise_pct']}%")
    log_event(f"  Biggest Win: {stats['biggest_win']:+.1f} BB | Biggest Loss: {stats['biggest_loss']:.1f} BB")

if __name__ == "__main__":
    main()
