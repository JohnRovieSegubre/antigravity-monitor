import re
import json

def extract_models():
    with open('gateway_server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    models = []
    
    for line in lines:
        line = line.strip()
        if not line.startswith('"sovereign/'): continue
        
        # Match ID, Price, Provider and Name
        id_match = re.search(r'"(sovereign/[^"]+)"', line)
        price_match = re.search(r'"price_sats":\s*(\d+)', line)
        comment_match = re.search(r'#\s*([^:]+):\s*(.*)', line)
        
        if id_match and price_match and comment_match:
            id = id_match.group(1)
            price_sats = int(price_match.group(1))
            provider = comment_match.group(1).strip()
            name = comment_match.group(2).strip()
            
            # Simple categorization logic
            category = "General"
            id_lower = id.lower()
            name_lower = name.lower()
            if any(x in id_lower or x in name_lower for x in ["coder", "code", "solidity"]):
                category = "Coding"
            elif any(x in id_lower or x in name_lower for x in ["think", "reasoning", "o1", "o3", "r1", "qwq"]):
                category = "Reasoning"
            elif any(x in id_lower or x in name_lower for x in ["vision", "vl", "image", "multimodal"]):
                category = "Vision"
            elif price_sats < 10:
                category = "Lite"

            models.append({
                "id": id,
                "name": name,
                "provider": provider,
                "price_usd": round(price_sats / 100000, 5),
                "category": category
            })

    # Sort by provider then name
    models.sort(key=lambda x: (x['provider'], x['name']))

    with open('landing/models_catalog.json', 'w') as f:
        json.dump(models, f, indent=2)
    
    print(f"Cleanly extracted {len(models)} models to landing/models_catalog.json")

if __name__ == "__main__":
    extract_models()
