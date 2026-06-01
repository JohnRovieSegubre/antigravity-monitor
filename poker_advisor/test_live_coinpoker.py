from vision import PokerVision
import json

v = PokerVision()
state = v.parse_state()
print("CURRENT VISION STATE:")
print(json.dumps(state, indent=2))
