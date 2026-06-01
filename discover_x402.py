import requests
import json

url = "https://api.sovereign-api.com/v1/x402/info"
print(f"📡 Discovery: {url}")
try:
    resp = requests.get(url, timeout=10)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"❌ Failed: {e}")
