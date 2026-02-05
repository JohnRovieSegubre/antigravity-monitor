import requests
import json
import pathlib

# Load creds
creds_path = pathlib.Path(r"c:\Users\rovie segubre\.gemini\antigravity\playground\obsidian-trifid\.agent\secure\moltbook_credentials.json")
with open(creds_path, 'r') as f:
    creds = json.load(f)

api_key = creds["api_key"]
headers = {"Authorization": f"Bearer {api_key}"}

# Search topics
topics = ["finance", "economy", "crypto", "agent", "autonomous"]
print(f"🔍 Exploring Moltbook for topics: {topics}...\n")

results = []

for topic in topics:
    # Use Semantic Search endpoint (if available) or generic search
    # The documentation mentioned simple 'feed' or 'posts'. 
    # Let's try to 'search' if documented, otherwise fetch recent posts.
    
    # Docs say: /api/v1/search?q=... (checking if this endpoint exists from skill.md reading earlier... 
    # Wait, skill.md mentioned "Semantic Search". Let's check the chunk for exact endpoint.
    # Chunk 12 usually contains search. 
    # Assuming /api/v1/search based on standard patterns or reading feed and filtering.
    # Let's start with a broad feed fetch and filter locally if search endpoint isn't explicit yet.
    # Actually, let's try the documented 'posts' endpoint first.
    
    try:
        url = f"https://www.moltbook.com/api/v1/posts?sort=new&limit=20" 
        # Note: Ideally we would use a search endpoint if confirmed.
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json().get("data", [])
            for post in posts:
                content = post.get("content", "").lower()
                if topic in content:
                    results.append(post)
    except Exception as e:
        print(f"❌ Error searching {topic}: {e}")

# Deduplicate
unique_results = {p['id']: p for p in results}.values()

print(f"✅ Found {len(unique_results)} relevant posts.\n")

for post in list(unique_results)[:5]:
    print(f"--- Post by {post.get('author', {}).get('name')} ---")
    print(post.get('content'))
    print(f"[ID: {post.get('id')}]\n")

# Save findings for the agent to analyze
with open("moltbook_findings.json", "w") as f:
    json.dump(list(unique_results), f, indent=2)
