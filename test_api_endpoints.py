import urllib.request, json, urllib.error

headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}

req_ping = urllib.request.Request('https://api.sovereign-api.com/v1/register/ping', headers=headers)
try:
    with urllib.request.urlopen(req_ping) as f:
        print("=== GET /v1/register/ping ===")
        print(f.read().decode())
except urllib.error.URLError as e:
    print(f"Ping Error: {e.reason}")

data = json.dumps({'name': 'urllib-test', 'description': 'Checking API response'}).encode('utf-8')
req_post = urllib.request.Request('https://api.sovereign-api.com/v1/register', data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req_post) as f:
        print("\n=== POST /v1/register ===")
        print(f.read().decode())
except urllib.error.HTTPError as e:
    print(f"\nPOST Error: {e.code} - {e.reason}")
    print(e.read().decode())

req_models = urllib.request.Request('https://api.sovereign-api.com/v1/models', headers=headers)
try:
    with urllib.request.urlopen(req_models) as f:
        print("\n=== GET /v1/models (first 200 chars) ===")
        print(f.read().decode()[:200])
except urllib.error.URLError as e:
    print(f"Models Error: {e.reason}")

req_model_specific = urllib.request.Request('https://api.sovereign-api.com/v1/models/sovereign/claude-3.5-haiku', headers=headers)
try:
    with urllib.request.urlopen(req_model_specific) as f:
        print("\n=== GET /v1/models/sovereign/claude-3.5-haiku ===")
        print(f.read().decode())
except urllib.error.URLError as e:
    print(f"Specific Model Error: {e.reason}")

completions_data = json.dumps({'model': 'sovereign/claude-3.5-haiku', 'prompt': 'Say hello'}).encode('utf-8')
req_completions = urllib.request.Request('https://api.sovereign-api.com/v1/completions', data=completions_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req_completions) as f:
        print("\n=== POST /v1/completions ===")
        print(f.code)
        # 401/402 is fine, just seeing if we get a Sovereign 401 instead of a 404
except urllib.error.HTTPError as e:
    print(f"\nPOST /v1/completions Status: {e.code}")

responses_data = json.dumps({'model': 'sovereign/claude-3.5-haiku', 'messages': [{'role': 'user', 'content': 'hello'}]}).encode('utf-8')
req_responses = urllib.request.Request('https://api.sovereign-api.com/v1/responses', data=responses_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req_responses) as f:
        print("\n=== POST /v1/responses ===")
        print(f.code)
except urllib.error.HTTPError as e:
    print(f"\nPOST /v1/responses Status: {e.code}")
