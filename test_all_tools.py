import requests
import json
import time

API_KEY = "sk-sov-97cd2d376195be7cec0b01da621030d8"
BASE_URL = "https://api.sovereign-api.com/v1/tools"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

TESTS = [
    ("crypto-price", "GET", {"ids": "bitcoin"}),
    ("market-data", "GET", {}),
    ("wallet-balance", "POST", {"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "chain": "ethereum"}),
    ("ens-resolve", "GET", {"name": "vitalik.eth"}),
    ("web-search", "POST", {"query": "Sovereign AI API"}),
    ("web-scrape", "GET", {"url": "https://example.com"}),
    ("web-screenshot", "GET", {"url": "https://example.com"}),
    ("flight-search", "GET", {"origin": "JFK", "destination": "LHR", "departureDate": "2026-05-01"}),
    ("hotel-search", "GET", {"q": "London", "checkInDate": "2026-05-01", "checkOutDate": "2026-05-05"}),
    ("image-gen", "POST", {"prompt": "A futuristic city"}),
    ("tts", "POST", {"text": "Hello world"}),
    ("transcription", "POST", {"audio_url": "https://www.w3schools.com/html/horse.mp3"}),
    ("code-exec", "POST", {"code": "print('Hello world')", "language": "python"}),
    ("embeddings", "POST", {"text": "Hello world"}),
]

print("Starting tool endpoint tests...\n")

for name, method, params in TESTS:
    url = f"{BASE_URL}/{name}"
    print(f"Testing {method} {name}...")
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=HEADERS, json=params, timeout=20)
            
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # print snippet of success
            success_status = data.get("success", False)
            print(f"Success Flag: {success_status}")
        else:
            print(f"Error Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
        
    print("-" * 40)
    time.sleep(1) # rate limit politeness

print("Done testing all endpoints.")
