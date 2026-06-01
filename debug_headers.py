import requests
import os
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")
api_key = os.getenv("SOVEREIGN_API_KEY")
url = "https://api.sovereign-api.com/v1/chat/completions"

headers = {
    "X-Sovereign-Api-Key": api_key,
    "Content-Type": "application/json"
}
payload = {
    "model": "sovereign/deepseek-r1",
    "messages": [{"role": "user", "content": "test"}]
}

print(f"📡 Hitting {url}...")
resp = requests.post(url, json=payload, headers=headers)
print(f"Status: {resp.status_code}")
print("Headers:")
for k, v in resp.headers.items():
    print(f"  {k}: {v}")
