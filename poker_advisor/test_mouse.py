import win32gui
import win32api
import time
import sys

def find_active_window():
    result = [None]
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if title == 'coinpoker' or 'freeroll' in title or 'nlh' in title or 'sunday' in title or 'step [' in title:
                if 'youtube' not in title and 'advisor' not in title:
                    result[0] = hwnd
                    return False
        return True
    win32gui.EnumWindows(callback, None)
    return result[0]

hwnd = find_active_window()
if not hwnd:
    print("Could not find CoinPoker window!")
    sys.exit()

left, top, right, bot = win32gui.GetWindowRect(hwnd)
w, h = right - left, bot - top

print("Moving mouse to test button coordinates...")

# Estimated Fold button
fold_x = left + int(w * 0.55)
fold_y = top + int(h * 0.92)

# Estimated Call button
call_x = left + int(w * 0.75)
call_y = top + int(h * 0.92)

# Estimated Raise button
raise_x = left + int(w * 0.90)
raise_y = top + int(h * 0.92)

print("Hovering over FOLD...")
win32api.SetCursorPos((fold_x, fold_y))
time.sleep(2)

print("Hovering over CALL/CHECK...")
win32api.SetCursorPos((call_x, call_y))
time.sleep(2)

print("Hovering over RAISE/BET...")
win32api.SetCursorPos((raise_x, raise_y))
time.sleep(2)

print("Done hovering.")
