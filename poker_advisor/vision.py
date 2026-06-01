import cv2
import numpy as np
import easyocr
import win32gui, win32ui, ctypes
import re
from equity import calculate_equity

class VisionClient:
    def __init__(self, hwnd, reader):
        self.hwnd = hwnd
        self.reader = reader

    def capture_screen(self):
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        w, h = right - left, bot - top
        if w == 0 or h == 0: return None
        
        hwndDC = win32gui.GetWindowDC(self.hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        ctypes.windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 2)
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype='uint8').reshape((h, w, 4))
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)
        
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def extract_text(self, img, rect, allowlist=None, thresh_inv=False):
        x1, y1, x2, y2 = rect
        crop = img[y1:y2, x1:x2]
        if crop.size == 0: return ""
        scale = 3
        crop_large = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(crop_large, cv2.COLOR_BGR2GRAY)
        
        if thresh_inv:
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        else:
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
        results = self.reader.readtext(thresh, allowlist=allowlist, detail=0)
        return " ".join(results)

    def parse_state(self):
        raise NotImplementedError()


class Vision888(VisionClient):
    def find_hero_cards_dynamic(self, img):
        h, w = img.shape[:2]
        y1, y2 = int(h * 0.5), int(h * 0.95)
        x1, x2 = int(w * 0.35), int(w * 0.65)
        roi = img[y1:y2, x1:x2]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_rects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.001): 
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch)
                if 1.0 <= aspect_ratio <= 2.2:
                    half_w = cw // 2
                    card_rects.append((x + x1, y + y1, half_w, ch))
                    card_rects.append((x + x1 + half_w, y + y1, half_w, ch))
                elif 0.3 <= aspect_ratio < 1.0:
                    card_rects.append((x + x1, y + y1, cw, ch))
                    
        card_rects = sorted(card_rects, key=lambda r: r[0])
        if len(card_rects) >= 2:
            return card_rects[:2]
        return None

    def read_card(self, img, rect):
        x, y, w, h = rect
        rank_y1, rank_y2 = y, y + int(h * 0.45)
        rank_x1, rank_x2 = x, x + int(w * 0.5)
        rank_crop = img[rank_y1:rank_y2, rank_x1:rank_x2]
        
        scale = 3
        rank_large = cv2.resize(rank_crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(rank_large, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
            
        results = self.reader.readtext(thresh, allowlist='0123456789AKQJToO', detail=0)
        rank = " ".join(results).replace('10', 'T').replace('0', 'Q').replace('O', 'Q').replace('o', 'Q')
        
        hsv_crop = cv2.cvtColor(rank_crop, cv2.COLOR_BGR2HSV)
        mask_red1 = cv2.inRange(hsv_crop, np.array([0, 70, 50]), np.array([10, 255, 255]))
        mask_red2 = cv2.inRange(hsv_crop, np.array([170, 70, 50]), np.array([180, 255, 255]))
        mask_black = cv2.inRange(hsv_crop, np.array([0, 0, 0]), np.array([180, 255, 100]))
        
        red_pixels = cv2.countNonZero(mask_red1) + cv2.countNonZero(mask_red2)
        black_pixels = cv2.countNonZero(mask_black)
        
        if red_pixels > 5 and red_pixels > black_pixels: suit = '♥'
        elif black_pixels > 5: suit = '♠'
        else: suit = '?'
        return rank, suit

    def find_community_cards_dynamic(self, img):
        h, w = img.shape[:2]
        # 888poker community cards are centered
        y1, y2 = int(h * 0.38), int(h * 0.58)
        x1, x2 = int(w * 0.35), int(w * 0.65)
        roi = img[y1:y2, x1:x2]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_rects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Community cards are medium-sized
            if area > (w * h * 0.002): 
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch)
                if 0.5 <= aspect_ratio <= 0.9:
                    card_rects.append((x + x1 + 2, y + y1 + 2, cw - 4, ch - 4))
                    
        return sorted(card_rects, key=lambda r: r[0])

    def parse_state(self):
        img = self.capture_screen()
        if img is None: return {"error": "Capture failed"}

        state = {}
        h, w = img.shape[:2]
        
        cards = self.find_hero_cards_dynamic(img)
        if cards:
            c1_rank, c1_suit = self.read_card(img, cards[0])
            c2_rank, c2_suit = self.read_card(img, cards[1])
            
            card_y = cards[0][1]
            card_h = cards[0][3]
            card_w = cards[0][2]
            
            stack_y1 = card_y + int(card_h * 1.1)
            stack_y2 = card_y + int(card_h * 1.9)
            stack_x1 = cards[0][0] - int(card_w * 0.2)
            stack_x2 = cards[1][0] + cards[1][2] + int(card_w * 0.2)
            
            stack_y1, stack_y2 = max(0, stack_y1), min(h, stack_y2)
            stack_x1, stack_x2 = max(0, stack_x1), min(w, stack_x2)
            
            stack_raw = self.extract_text(img, (stack_x1, stack_y1, stack_x2, stack_y2))
        else:
            c1_rank, c1_suit = "?", "?"
            c2_rank, c2_suit = "?", "?"
            stack_raw = ""
            
        if c1_rank: c1_rank = c1_rank.replace('10', 'T').replace('0', 'Q')
        if c2_rank: c2_rank = c2_rank.replace('10', 'T').replace('0', 'Q')
        
        c1_color = 'red' if c1_suit == '♥' else 'blue' if c1_suit == '♦' else 'green' if c1_suit == '♣' else 'black'
        c2_color = 'red' if c2_suit == '♥' else 'blue' if c2_suit == '♦' else 'green' if c2_suit == '♣' else 'black'
        
        state['hero_cards'] = [
            {"rank": c1_rank, "suit": c1_suit, "color": c1_color},
            {"rank": c2_rank, "suit": c2_suit, "color": c2_color}
        ]

        board_rects = self.find_community_cards_dynamic(img)
        board_cards = []
        for r in board_rects:
            r_rank, r_suit = self.read_card(img, r)
            if r_rank: r_rank = r_rank.replace('10', 'T').replace('0', 'Q')
            c_color = 'red' if r_suit in ['♥'] else 'blue' if r_suit == '♦' else 'green' if r_suit == '♣' else 'black'
            board_cards.append({"rank": r_rank, "suit": r_suit, "color": c_color})
        state['board_cards'] = board_cards

        target_w, target_h = 1117, 860
        sx, sy = w / target_w, h / target_h
        pot_raw = self.extract_text(img, (int(400*sx), int(330*sy), int(680*sx), int(365*sy)))
        pot_match = re.search(r'([\d.]+)', pot_raw)
        state['pot'] = float(pot_match.group(1)) if pot_match else 0.0

        stack_match = re.search(r'([\d.]+)', stack_raw.replace(',', ''))
        state['stack'] = float(stack_match.group(1)) if stack_match else 0.0

        # Detect to_call from the call button text (e.g. "Call 2 BB")
        call_btn_raw = self.extract_text(img, (int(w*0.80), int(h*0.92), int(w*0.95), int(h*0.98)))
        call_match = re.search(r'([\d.]+)', call_btn_raw)
        state['to_call'] = float(call_match.group(1)) if call_match else 0.0

        eq_result = calculate_equity(state['hero_cards'], state['board_cards'], num_opponents=2, simulations=500)
        equity = eq_result['equity']
        
        state['equity'] = equity
        state['hand_class'] = eq_result['hand_class']
        state['stage'] = eq_result['stage']
        
        # Use strategy engine if available, fallback to simple thresholds
        try:
            from strategy import decide
            decision = decide(equity, state['pot'], state['to_call'], state['stack'], state['stage'], state['hand_class'])
            state['action'] = decision['action']
            state['ev_estimate'] = decision['ev_estimate']
            state['pot_odds'] = decision['pot_odds']
            state['spr'] = decision['spr']
            state['reasoning'] = decision['reasoning']
        except Exception:
            if equity == 0: state['action'] = "WAITING"
            elif equity > 65: state['action'] = 'RAISE'
            elif equity > 45: state['action'] = 'CALL'
            else: state['action'] = 'FOLD'
            state['ev_estimate'] = 0.0
            state['pot_odds'] = 0.0
            state['spr'] = 0.0
            state['reasoning'] = ''

        state['client'] = "888poker"
        return state


class VisionCoinPoker(VisionClient):
    def find_hero_cards_dynamic(self, img):
        h, w = img.shape[:2]
        # CoinPoker cards are centered in the bottom half
        y1, y2 = int(h * 0.6), int(h * 0.95)
        x1, x2 = int(w * 0.35), int(w * 0.65)
        roi = img[y1:y2, x1:x2]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_rects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # CoinPoker cards are relatively large
            if area > (w * h * 0.005): 
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch)
                # Overlapping tilted cards will form a wide bounding box
                if 1.0 <= aspect_ratio <= 2.2:
                    half_w = cw // 2
                    card_rects.append((x + x1, y + y1, half_w, ch))
                    card_rects.append((x + x1 + half_w, y + y1, half_w, ch))
                elif 0.3 <= aspect_ratio < 1.0:
                    card_rects.append((x + x1, y + y1, cw, ch))
                    
        card_rects = sorted(card_rects, key=lambda r: r[0])
        if len(card_rects) >= 2:
            return card_rects[:2]
        return None

    def find_community_cards_dynamic(self, img):
        h, w = img.shape[:2]
        # Community cards are in the direct center
        y1, y2 = int(h * 0.35), int(h * 0.6)
        x1, x2 = int(w * 0.2), int(w * 0.8)
        roi = img[y1:y2, x1:x2]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_rects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Community cards are slightly smaller than hole cards
            if area > (w * h * 0.003): 
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = cw / float(ch)
                # Community cards are vertical and separated
                if 0.5 <= aspect_ratio <= 0.85:
                    # Tighten the crop by 2 pixels on all sides to avoid capturing the green table background
                    card_rects.append((x + x1 + 2, y + y1 + 2, cw - 4, ch - 4))
                    
        # Sort left to right
        return sorted(card_rects, key=lambda r: r[0])

    def read_card(self, img, rect):
        x, y, w, h = rect
        # Give enough room for wide characters like Q
        rank_y1, rank_y2 = y, y + int(h * 0.5)
        rank_x1, rank_x2 = x, x + int(w * 0.55)
        rank_crop = img[rank_y1:rank_y2, rank_x1:rank_x2]
        
        scale = 3
        rank_large = cv2.resize(rank_crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(rank_large, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
            
        results = self.reader.readtext(thresh, allowlist='0123456789AKQJToO', detail=0)
        rank = " ".join(results).replace('10', 'T').replace('0', 'Q').replace('O', 'Q').replace('o', 'Q')
        rank = rank.replace('22', '2').replace('1', '7')
        
        hsv_crop = cv2.cvtColor(rank_crop, cv2.COLOR_BGR2HSV)
        mask_red1 = cv2.inRange(hsv_crop, np.array([0, 70, 50]), np.array([10, 255, 255]))
        mask_red2 = cv2.inRange(hsv_crop, np.array([170, 70, 50]), np.array([180, 255, 255]))
        mask_black = cv2.inRange(hsv_crop, np.array([0, 0, 0]), np.array([180, 255, 100]))
        
        red_p = cv2.countNonZero(mask_red1) + cv2.countNonZero(mask_red2)
        black_p = cv2.countNonZero(mask_black)
        
        if red_p > 5 and red_p > black_p:
            suit = '♥'
        elif black_p > 5:
            suit = '♠'
        else:
            suit = '?'
            
        return rank, suit

    def parse_state(self):
        img = self.capture_screen()
        if img is None: return {"error": "Capture failed"}

        state = {}
        h, w = img.shape[:2]
        
        cards = self.find_hero_cards_dynamic(img)
        if cards:
            c1_rank, c1_suit = self.read_card(img, cards[0])
            c2_rank, c2_suit = self.read_card(img, cards[1])
            
            # Stack size is under the cards in the nameplate.
            # E.g. "pokeradict\n52.09BB"
            card_y = cards[0][1]
            card_h = cards[0][3]
            card_w = cards[0][2]
            
            stack_y1 = card_y + int(card_h * 1.0)
            stack_y2 = card_y + int(card_h * 2.2)
            stack_x1 = cards[0][0] - int(card_w * 0.5)
            stack_x2 = cards[1][0] + cards[1][2] + int(card_w * 0.5)
            
            stack_y1, stack_y2 = max(0, stack_y1), min(h, stack_y2)
            stack_x1, stack_x2 = max(0, stack_x1), min(w, stack_x2)
            
            # CoinPoker stack text is yellow or white on dark grey
            stack_raw = self.extract_text(img, (stack_x1, stack_y1, stack_x2, stack_y2), thresh_inv=True)
        else:
            c1_rank, c1_suit = "?", "?"
            c2_rank, c2_suit = "?", "?"
            stack_raw = ""
            
        if c1_rank: c1_rank = c1_rank.replace('10', 'T').replace('0', 'Q')
        if c2_rank: c2_rank = c2_rank.replace('10', 'T').replace('0', 'Q')
        
        c1_color = 'red' if c1_suit == '♥' else 'blue' if c1_suit == '♦' else 'green' if c1_suit == '♣' else 'black'
        c2_color = 'red' if c2_suit == '♥' else 'blue' if c2_suit == '♦' else 'green' if c2_suit == '♣' else 'black'
        
        state['hero_cards'] = [
            {"rank": c1_rank, "suit": c1_suit, "color": c1_color},
            {"rank": c2_rank, "suit": c2_suit, "color": c2_color}
        ]

        board_rects = self.find_community_cards_dynamic(img)
        board_cards = []
        for r in board_rects:
            r_rank, r_suit = self.read_card(img, r)
            if r_rank: r_rank = r_rank.replace('10', 'T').replace('0', 'Q')
            c_color = 'red' if r_suit in ['♥'] else 'blue' if r_suit == '♦' else 'green' if r_suit == '♣' else 'black'
            board_cards.append({"rank": r_rank, "suit": r_suit, "color": c_color})
        state['board_cards'] = board_cards

        # Pot size in CoinPoker is directly in the center of the screen
        # e.g. "Pot 1.98BB"
        pot_raw = self.extract_text(img, (int(w*0.35), int(h*0.35), int(w*0.65), int(h*0.5)), thresh_inv=True)
        pot_match = re.search(r'(?:Pot)?\s*([\d.]+)', pot_raw)
        state['pot'] = float(pot_match.group(1)) if pot_match else 0.0

        stack_match = re.search(r'([\d.]+)', stack_raw.replace(',', ''))
        state['stack'] = float(stack_match.group(1)) if stack_match else 0.0

        # Detect to_call from the call button text area
        call_btn_raw = self.extract_text(img, (int(w*0.65), int(h*0.88), int(w*0.85), int(h*0.97)), thresh_inv=True)
        call_match = re.search(r'([\d.]+)', call_btn_raw)
        state['to_call'] = float(call_match.group(1)) if call_match else 0.0

        eq_result = calculate_equity(state['hero_cards'], state['board_cards'], num_opponents=2, simulations=500)
        equity = eq_result['equity']
        
        state['equity'] = equity
        state['hand_class'] = eq_result['hand_class']
        state['stage'] = eq_result['stage']
        
        # Use strategy engine if available, fallback to simple thresholds
        try:
            from strategy import decide
            decision = decide(equity, state['pot'], state['to_call'], state['stack'], state['stage'], state['hand_class'])
            state['action'] = decision['action']
            state['ev_estimate'] = decision['ev_estimate']
            state['pot_odds'] = decision['pot_odds']
            state['spr'] = decision['spr']
            state['reasoning'] = decision['reasoning']
        except Exception:
            if equity == 0: state['action'] = "WAITING"
            elif equity > 65: state['action'] = 'RAISE'
            elif equity > 45: state['action'] = 'CALL'
            else: state['action'] = 'FOLD'
            state['ev_estimate'] = 0.0
            state['pot_odds'] = 0.0
            state['spr'] = 0.0
            state['reasoning'] = ''

        state['client'] = "CoinPoker"
        return state


class PokerVision:
    def __init__(self):
        print("Initializing Vision Engine (loading OCR)...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        self.client = None
        self.client_type = None
        print("Vision Engine Ready.")

    def find_active_window(self):
        import win32process
        import psutil
        
        result = [None]
        client_type = [None]
        
        def callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if not title.strip():
                        return True
                    
                    # Ignore browser windows, advisor itself, youtube, etc.
                    if any(w in title for w in ['youtube', 'advisor', 'edge', 'chrome', 'firefox', 'opera', 'safari']):
                        return True
                    
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        proc_name = proc.name().lower()
                    except Exception:
                        return True
                    
                    # Check for 888poker
                    if 'poker.exe' in proc_name:
                        # Table titles have 'blinds:', 'table #', 'id #', 'freeroll', or 'nlh'
                        if any(w in title for w in ['blinds:', 'table #', 'id #', 'freeroll', 'nlh']):
                            result[0] = hwnd
                            client_type[0] = "888"
                            return False
                    
                    # Check for CoinPoker
                    elif 'coinpoker.exe' in proc_name:
                        left, top, right, bot = win32gui.GetWindowRect(hwnd)
                        w, h = right - left, bot - top
                        # Skip the hand history popups
                        if 'hand history' in title:
                            return True
                        
                        # Lobby is usually 1280x778. Tables are resizable.
                        # We'll avoid the exact lobby dimensions, or if we must, we pick it.
                        if w != 1280 and h != 778:
                            result[0] = hwnd
                            client_type[0] = "CoinPoker"
                            return False
                        
                        # Fallback if no other window found yet
                        if not result[0]:
                            result[0] = hwnd
                            client_type[0] = "CoinPoker"
            except Exception:
                pass
            return True
        
        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass
        return result[0], client_type[0]

    def parse_state(self):
        hwnd, c_type = self.find_active_window()
        if not hwnd:
            self.client = None
            self.client_type = None
            return {"error": "Poker table not found"}
            
        if self.client_type != c_type:
            print(f"Detected {c_type} client!")
            self.client_type = c_type
            if c_type == "888":
                self.client = Vision888(hwnd, self.reader)
            elif c_type == "CoinPoker":
                self.client = VisionCoinPoker(hwnd, self.reader)
                
        # Delegated parsing to the active client engine
        return self.client.parse_state()
