#!/usr/bin/env python3
"""
Inspect CxC Schema
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

def inspect_cxc():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    response = requests.post(
        f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query",
        headers=headers,
        json={"page_size": 1}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    results = response.json().get("results", [])
    if results:
        print(json.dumps(results[0].get("properties"), indent=2))
    else:
        print("No items found.")

if __name__ == "__main__":
    inspect_cxc()

