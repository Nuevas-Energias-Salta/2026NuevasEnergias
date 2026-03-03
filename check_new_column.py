#!/usr/bin/env python3
"""
Inspect CxP Schema for 'Monto Dolares'
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def check_new_column():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    response = requests.post(
        f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
        headers=headers,
        json={"page_size": 1}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    results = response.json().get("results", [])
    if results:
        props = results[0].get("properties", {})
        
        # Check specific column variations
        candidates = ["Monto Dolares", "Monto Dólares", "monto dolares", "USD"]
        found = False
        
        for key in props.keys():
            if any(cand.lower() in key.lower() for cand in candidates):
                print(f"FOUND COLUMN: '{key}' ({props[key]['type']})")
                found = True
        
        if not found:
            print("Column 'Monto Dolares' NOT found in properties:")
            print(list(props.keys()))

if __name__ == "__main__":
    check_new_column()

