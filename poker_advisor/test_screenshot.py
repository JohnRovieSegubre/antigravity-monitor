import win32gui
import win32ui
import ctypes
import numpy as np
import cv2
import sys
sys.path.append(r"C:\Users\rovie segubre\agent\poker_advisor")
from vision import PokerVision

v = PokerVision()
hwnd, client = v.find_active_window()

if hwnd:
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

    cv2.imwrite("C:/Users/rovie segubre/solitaire_recon/live_test.png", img)
    print("Saved live screenshot to live_test.png")
