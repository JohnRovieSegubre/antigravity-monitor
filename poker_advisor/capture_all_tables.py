import win32gui, win32ui, ctypes
import numpy as np
import cv2

hwnds = [788758, 918938]

for i, hwnd in enumerate(hwnds):
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        w, h = right - left, bot - top
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype='uint8').reshape((h, w, 4))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        path = f"C:/Users/rovie segubre/solitaire_recon/table_{i+1}.png"
        cv2.imwrite(path, img)
        print(f"Saved table {i+1} (HWND {hwnd}) to table_{i+1}.png")
    except Exception as e:
        print(f"Error capturing HWND {hwnd}: {e}")
