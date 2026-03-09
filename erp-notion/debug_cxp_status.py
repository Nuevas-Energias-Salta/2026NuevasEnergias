#!/usr/bin/env python3
"""
Inspect unique 'Estado' values in CxP database
"""

import requests
import json
from collections import Counter

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def get_cxp_statuses():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print(f"Querying CxP database ({CXP_DB_ID})...")
    
    all_statuses = []
    has_more = True
    next_cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
            
        response = requests.post(
            f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break
            
        data = response.json()
        results = data.get("results", [])
        
        for item in results:
            props = item.get("properties", {})
            status_obj = props.get("Estado", {}).get("select", {})
            if status_obj:
                all_statuses.append(status_obj.get("name", "Unknown"))
            else:
                all_statuses.append("None")
                
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
    
    print("\nUnique Statuses found:")
    counts = Counter(all_statuses)
    for status, count in counts.items():
        print(f"'{status}': {count}")

if __name__ == "__main__":
    get_cxp_statuses()

