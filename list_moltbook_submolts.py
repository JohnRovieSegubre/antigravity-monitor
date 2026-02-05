import requests
import json
import pathlib

# Load creds
creds_path = pathlib.Path(r"c:\Users\rovie segubre\.gemini\antigravity\playground\obsidian-trifid\.agent\secure\moltbook_credentials.json")
with open(creds_path, 'r') as f:
    creds = json.load(f)

api_key = creds["api_key"]
headers = {"Authorization": f"Bearer {api_key}"}

url = "https://www.moltbook.com/api/v1/submolts"

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print("--- Available Submolts ---")
    data = response.json().get("data", [])
    for sub in data:
        print(f"🦞 {sub['name']} ({sub['slug']}) - {sub['description']}")
except Exception as e:
    print(f"❌ Error: {e}")
    if 'response' in locals():
        print(response.text)
