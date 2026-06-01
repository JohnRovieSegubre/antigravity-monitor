import time
import win32gui
import win32api
import win32con
import sys
import random
sys.path.append(r"C:\Users\rovie segubre\agent\poker_advisor")
from vision import PokerVision

print("Initializing Antigravity Execution Bot (LIVE PLAY MODE)...")
v = PokerVision()

def human_click(x, y):
    # Add random jitter so it doesn't click the exact same pixel
    x += random.randint(-5, 5)
    y += random.randint(-5, 5)
    
    win32api.SetCursorPos((x, y))
    time.sleep(random.uniform(0.1, 0.3)) # Human reaction time
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(random.uniform(0.05, 0.15)) # Click duration
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

print("Bot is now actively watching and PLAYING the table... Take your hands off the mouse!")
last_click_time = 0

while True:
    try:
        hwnd, client = v.find_active_window()
        if hwnd:
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            w, h = right - left, bot - top
            
            # Button coordinates based on our hover test
            fold_x, fold_y = left + int(w * 0.55), top + int(h * 0.92)
            call_x, call_y = left + int(w * 0.75), top + int(h * 0.92)
            raise_x, raise_y = left + int(w * 0.90), top + int(h * 0.92)

            state = v.parse_state()
            action = state.get('action', 'WAITING')
            
            # We only act if we have cards (stack > 0 prevents clicking when folded)
            # and if we haven't clicked in the last 5 seconds to prevent spamming
            if action != 'WAITING' and state.get('stack', 0) > 0 and (time.time() - last_click_time > 5):
                print(f"[{time.strftime('%H:%M:%S')}] Executing Action: {action}! Equity: {state.get('equity')}%")
                
                # Add a randomized human delay before acting
                time.sleep(random.uniform(1.0, 3.5))
                
                if action == 'FOLD':
                    human_click(fold_x, fold_y)
                elif action == 'CALL':
                    human_click(call_x, call_y)
                elif action == 'RAISE':
                    human_click(raise_x, raise_y)
                
                last_click_time = time.time()
                    
        time.sleep(2)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
