from vision import PokerVision
import json

try:
    v = PokerVision()
    state = v.parse_state()
    print("CURRENT VISION STATE:")
    print(json.dumps(state, indent=2))
except Exception as e:
    print(f"Error: {e}")
