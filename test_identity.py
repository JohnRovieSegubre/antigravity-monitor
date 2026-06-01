import requests
import os
from dotenv import load_dotenv

load_dotenv("sovereign-openclaw/.env")
api_key = os.getenv("SOVEREIGN_API_KEY")
url = os.getenv("GATEWAY_URL") + "/models"

print(f"📡 Testing Key: {api_key[:12]}...")
headers = {"X-Sovereign-Api-Key": api_key}
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"❌ Failed: {e}")
