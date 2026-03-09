#!/usr/bin/env python3
"""
Inspect a single CxP item with Status='Pagado'
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def inspect_cxp_item():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Filter for one item with Status = Pagado
    payload = {
        "page_size": 1,
        "filter": {
            "property": "Estado",
            "select": {
                "equals": "Pagado"
            }
        }
    }
            
    response = requests.post(
        f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
        headers=headers,
        json=payload
    )
    
    data = response.json()
    results = data.get("results", [])
    
    if results:
        item = results[0]
        print(json.dumps(item.get("properties"), indent=2))
    else:
        print("No 'Pagado' items found.")

if __name__ == "__main__":
    inspect_cxp_item()

