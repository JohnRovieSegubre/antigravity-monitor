import time
import sys
import json
from vision import PokerVision

print("Starting LLM Supervisory Loop...")
v = PokerVision()

last_state = None

while True:
    try:
        state = v.parse_state()
        
        # Only print if state has changed meaningfully to avoid spam
        current_summary = f"Pot: {state.get('pot')}, Stack: {state.get('stack')}, Action: {state.get('action')}, Board: {len(state.get('board_cards', []))} cards"
        
        if current_summary != last_state:
            print("\n--- NEW STATE DETECTED ---")
            print(json.dumps(state, indent=2))
            
            # Here I (the LLM) can inject my logic
            if state.get('stack', 0) > 0 and len(state.get('hero_cards', [])) == 2:
                print(">>> It looks like we are in a hand!")
                if len(state.get('board_cards', [])) == 3:
                    print(">>> FLOP is dealt! I am analyzing the community cards...")
                elif len(state.get('board_cards', [])) == 4:
                    print(">>> TURN is dealt!")
                elif len(state.get('board_cards', [])) == 5:
                    print(">>> RIVER is dealt!")
                    
            last_state = current_summary
            
        time.sleep(3) # Wait 3 seconds before next check
        
    except Exception as e:
        print(f"Error in supervisory loop: {e}")
        time.sleep(3)
