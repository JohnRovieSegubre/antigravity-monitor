import win32gui, win32process, sys
import psutil

sys.stdout.reconfigure(encoding='utf-8')

results = []
def cb(hwnd, _):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title.strip():
            results.append((hwnd, title))
    return True

win32gui.EnumWindows(cb, None)

for hwnd, title in results:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        pname = psutil.Process(pid).name().lower()
        if 'coinpoker' in pname or 'poker' in pname:
            print(f"Title: '{title}' | Process: {pname}")
    except Exception:
        pass
