import cv2
from vision import VisionCoinPoker
import easyocr
import json

reader = easyocr.Reader(['en'], gpu=False)
v = VisionCoinPoker(None, reader)

img = cv2.imread("C:/Users/rovie segubre/solitaire_recon/coinpoker_flop.png")

# find community cards
board_rects = v.find_community_cards_dynamic(img)
print(f"Found {len(board_rects)} community cards.")

board_cards = []
for r in board_rects:
    r_rank, r_suit = v.read_card(img, r)
    if r_rank: r_rank = r_rank.replace('10', 'T').replace('0', 'Q')
    board_cards.append({"rank": r_rank, "suit": r_suit})

print("BOARD CARDS:")
print(json.dumps(board_cards, indent=2))
