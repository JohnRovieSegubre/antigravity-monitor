from vision import VisionCoinPoker
import easyocr
import cv2
import json

reader = easyocr.Reader(['en'], gpu=False)
v = VisionCoinPoker(None, reader)

img = cv2.imread("C:/Users/rovie segubre/solitaire_recon/cross_reference.png")

# Use the exact same logic as parse_state to analyze this specific image
h, w = img.shape[:2]

# Hero Cards
cards = v.find_hero_cards_dynamic(img)
c1_rank, c1_suit = "?", "?"
c2_rank, c2_suit = "?", "?"
if cards:
    c1_rank, c1_suit = v.read_card(img, cards[0])
    c2_rank, c2_suit = v.read_card(img, cards[1])

# Board Cards
board_rects = v.find_community_cards_dynamic(img)
board_cards = []
for r in board_rects:
    r_rank, r_suit = v.read_card(img, r)
    board_cards.append(f"{r_rank}{r_suit}")

# Pot
pot_raw = v.extract_text(img, (int(w*0.4), int(h*0.3), int(w*0.6), int(h*0.4)))

print(f"Algorithm Analysis of cross_reference.png:")
print(f"Hero Cards: {c1_rank}{c1_suit}, {c2_rank}{c2_suit}")
print(f"Board Cards: {board_cards}")
print(f"Pot Region Text: {pot_raw}")
