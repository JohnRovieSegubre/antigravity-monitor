import urllib.request, json, urllib.error
import sys

API_KEY = "sk-sov-df8420680418af25dda11ffea2d35130"
headers = {
    'Content-Type': 'application/json', 
    'User-Agent': 'Mozilla/5.0',
    'Authorization': f'Bearer {API_KEY}'
}

print(f"Testing Key: {API_KEY}\n")

requests_to_make = [
    {
        "url": "https://api.sovereign-api.com/v1/chat/completions",
        "payload": {
            "model": "claude-3.5-haiku",  # Testing BARE NAME aliasing
            "messages": [{"role": "user", "content": "Say 'Test OK'"}],
            "max_tokens": 16
        }
    },
    {
        "url": "https://api.sovereign-api.com/v1/completions",
        "payload": {
            "model": "sovereign/claude-3.5-haiku",
            "prompt": "Say 'Test OK'",
            "max_tokens": 16
        }
    },
    {
        "url": "https://api.sovereign-api.com/v1/responses",
        "payload": {
            "model": "sovereign/claude-3.5-haiku",
            "input": "Say 'Test OK'",
            "max_tokens": 16
        }
    }
]

for req_data in requests_to_make:
    url = req_data["url"]
    payload = json.dumps(req_data["payload"]).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as f:
            print(f"[{url}] -> 200 OK")
    except urllib.error.HTTPError as e:
        print(f"[{url}] -> {e.code} - {e.read().decode()}")
    except Exception as e:
        print(f"[{url}] -> ERROR - {str(e)}")
