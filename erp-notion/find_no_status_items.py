#!/usr/bin/env python3
"""
Find items with No Status in CxP
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def find_no_status():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Filter for items with No Status
    # Empty select is hard to filter directly sometimes, fetch all and check
    
    print(f"Scanning for items with no status...")
    
    has_more = True
    next_cursor = None
    count = 0
    
    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
            
        response = requests.post(
            f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
            headers=headers,
            json=payload
        )
        
        data = response.json()
        results = data.get("results", [])
        
        for item in results:
            props = item.get("properties", {})
            status_obj = props.get("Estado", {}).get("select", {})
            
            if not status_obj:
                title_prop = props.get("Factura n°", {}).get("title", [])
                title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
                monto = props.get("Monto", {}).get("number", 0) or 0
                
                print(f"Found Item No Status: {title} | Monto: {monto}")
                count += 1
                
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
        
    print(f"Total items with no status: {count}")

if __name__ == "__main__":
    find_no_status()

