import win32gui

results = []

def callback(hwnd, _):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title.strip():
            try:
                results.append((hwnd, title))
            except:
                pass

win32gui.EnumWindows(callback, None)

print("ALL VISIBLE WINDOWS:")
print("-" * 80)
for hwnd, title in results:
    tl = title.lower()
    if 'coinpoker' in tl or 'nlh' in tl or 'freeroll' in tl or '888' in tl or 'poker' in tl:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        print(f"  HWND: {hwnd} | Size: {right-left}x{bot-top} | Title: {title}")
