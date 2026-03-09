#!/usr/bin/env python3
"""
Check if 'Monto base' is used in CxP and differs from 'Monto'
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def check_monto_base():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print(f"Scanning CxP for Monto base usage...")
    
    payload = {
        "page_size": 100,
        # Fetch items where "Monto base" is not empty/null if possible, 
        # but Notion filtering on number emptiness is tricky. Fetch all and iterate.
    }
    
    response = requests.post(
        f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
        headers=headers,
        json=payload
    )
    
    data = response.json()
    results = data.get("results", [])
    
    count_with_base = 0
    
    print(f"{'Title':<30} | {'Monto':<12} | {'Monto base':<12} | {'Diff':<10}")
    print("-" * 75)
    
    for item in results:
        props = item.get("properties", {})
        
        # Title
        title_prop = props.get("Factura n°", {}).get("title", [])
        title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
        
        # Montos
        monto = props.get("Monto", {}).get("number", 0) or 0
        monto_base = props.get("Monto base", {}).get("number") # None if null
        
        if monto_base is not None:
            count_with_base += 1
            print(f"{title[:30]:<30} | {monto:<12} | {monto_base:<12} | {monto - monto_base:<10.2f}")
            
    print("-" * 75)
    print(f"Total items inspected: {len(results)}")
    print(f"Items with 'Monto base': {count_with_base}")

if __name__ == "__main__":
    check_monto_base()

