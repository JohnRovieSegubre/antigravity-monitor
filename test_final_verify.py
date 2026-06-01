import requests

print('=== /v1/register/ping ===')
r = requests.get('https://api.sovereign-api.com/v1/register/ping', timeout=10)
print(f'{r.status_code}: {r.text[:200]}')

print('\n=== /v1/register (normal) ===')
r2 = requests.post('https://api.sovereign-api.com/v1/register', json={'name': 'verify-test'}, timeout=10)
print(f'{r2.status_code}: {r2.text[:300]}')

print('\n=== /v1/register (with BOM bytes) ===')
bom_body = b'\xef\xbb\xbf{"name": "bom-test"}\r\n'
r3 = requests.post('https://api.sovereign-api.com/v1/register', data=bom_body,
                    headers={'Content-Type': 'application/json'}, timeout=10)
print(f'{r3.status_code}: {r3.text[:300]}')

print('\n=== llm.txt ===')
r4 = requests.get('https://api.sovereign-api.com/llm.txt', timeout=10)
print(f'{r4.status_code}, len={len(r4.text)}, has_prepaid={"Prepaid" in r4.text}')
print(r4.text[:200])

print('\n=== skill.md ===')
r5 = requests.get('https://api.sovereign-api.com/skill.md', timeout=10)
print(f'{r5.status_code}, len={len(r5.text)}, has_matrix={"Auth Matrix" in r5.text}')
print(r5.text[:200])
