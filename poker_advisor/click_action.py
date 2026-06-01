import win32gui, win32api, win32con, time, sys
import random

if len(sys.argv) < 2:
    print("Usage: python click_action.py <FOLD|CALL|RAISE>")
    sys.exit(1)

action = sys.argv[1].upper()
sys.path.append(r"C:\Users\rovie segubre\agent\poker_advisor")
from vision import PokerVision

v = PokerVision()
hwnd, client = v.find_active_window()

def human_click(x, y):
    x += random.randint(-5, 5)
    y += random.randint(-5, 5)
    win32api.SetCursorPos((x, y))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

if hwnd:
    # win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bot - top
    
    if client == '888':
        if action == 'FOLD':
            x, y = left + int(w * 0.76), top + int(h * 0.95)
        elif action == 'CALL':
            x, y = left + int(w * 0.85), top + int(h * 0.95)
        elif action == 'RAISE':
            x, y = left + int(w * 0.94), top + int(h * 0.95)
        else:
            sys.exit(1)
    else: # CoinPoker
        if action == 'FOLD':
            x, y = left + int(w * 0.55), top + int(h * 0.92)
        elif action == 'CALL':
            x, y = left + int(w * 0.75), top + int(h * 0.92)
        elif action == 'RAISE':
            x, y = left + int(w * 0.90), top + int(h * 0.92)
        else:
            sys.exit(1)
        
    print(f"I am physically clicking {action} at ({x}, {y})...")
    human_click(x, y)
    print("Done!")
else:
    print("Could not find table window.")
