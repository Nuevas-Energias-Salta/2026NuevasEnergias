import requests
import json
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def check_schema():
    url = f"https://api.notion.com/v1/databases/{CXP_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        data = res.json()
        props = data.get("properties", {})
        print("=== PROPIEDADES DISPONIBLES (repr) ===")
        for name in props.keys():
            print(f"{name} -> {repr(name)}")
    else:
        print(f"Error: {res.text}")

if __name__ == "__main__":
    check_schema()

