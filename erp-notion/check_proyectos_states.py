import requests
import json

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

print("Checking PROYECTOS_DB_ID states...")
response = requests.post(f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query", headers=headers, json={"page_size": 100})
if response.status_code == 200:
    results = response.json().get("results", [])
    states = {}
    for p in results:
        status = p["properties"].get("Estado", {}).get("select", {})
        val = status.get("name", "N/A") if status else "N/A"
        states[val] = states.get(val, 0) + 1
    print(json.dumps(states, indent=2))
else:
    print(f"Error: {response.status_code}")

