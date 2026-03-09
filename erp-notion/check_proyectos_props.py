import requests
import json

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

print("Checking PROYECTOS_DB_ID properties...")
response = requests.get(f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}", headers=headers)
if response.status_code == 200:
    props = response.json().get("properties", {})
    for name, data in props.items():
        print(f" - {name}: {data['type']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

