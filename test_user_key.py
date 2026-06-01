import urllib.request, json, urllib.error
import sys

API_KEY = "sk-sov-df8420680418af25dda11ffea2d35130"
headers = {
    'Content-Type': 'application/json', 
    'User-Agent': 'Mozilla/5.0',
    'Authorization': f'Bearer {API_KEY}'
}

# We expect 403 because it's a new, unfunded key. We just want to see it hit OUR gateway logic.

payload = json.dumps({'model': 'sovereign/claude-3.5-haiku', 'messages': [{'role': 'user', 'content': 'hello'}]}).encode('utf-8')

endpoints = [
    '/v1/chat/completions',
    '/v1/completions',
    '/v1/responses'
]

print(f"Testing Key: {API_KEY}")

for ep in endpoints:
    url = f'https://api.sovereign-api.com{ep}'
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as f:
            print(f"[{ep}]: 200 OK")
    except urllib.error.HTTPError as e:
        print(f"[{ep}]: {e.code} - {e.read().decode()}")
    except Exception as e:
        print(f"[{ep}]: ERROR - {str(e)}")
