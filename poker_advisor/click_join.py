import win32gui
import win32api
import win32con
import time
import sys
sys.path.append(r"C:\Users\rovie segubre\agent\poker_advisor")
from vision import PokerVision

print("Finding CoinPoker window to click 'Join Now'...")
v = PokerVision()
hwnd, client = v.find_active_window()

if hwnd:
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bot - top
    
    # The green "Join Now" button is in the bottom right corner, 
    # exactly where the RAISE button usually is.
    join_x = left + int(w * 0.90)
    join_y = top + int(h * 0.92)
    
    print(f"Clicking 'Join Now' at ({join_x}, {join_y})...")
    
    win32api.SetCursorPos((join_x, join_y))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, join_x, join_y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, join_x, join_y, 0, 0)
    
    # Also click the modal 'Join Now' just in case
    modal_join_x = left + int(w * 0.40)
    modal_join_y = top + int(h * 0.60)
    
    print(f"Clicking modal 'Join Now' at ({modal_join_x}, {modal_join_y})...")
    
    win32api.SetCursorPos((modal_join_x, modal_join_y))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, modal_join_x, modal_join_y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, modal_join_x, modal_join_y, 0, 0)
    
    print("Done clicking! You should be back in the game.")
else:
    print("Could not find CoinPoker window.")
