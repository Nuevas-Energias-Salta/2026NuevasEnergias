#!/usr/bin/env python3
"""
Check if 'Pendiente' items have Monto Asignado Total > 0
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def check_pendiente():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Filter for items with Status = Pendiente
    payload = {
        "page_size": 100,
        "filter": {
            "property": "Estado",
            "select": {
                "equals": "Pendiente"
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
    
    print(f"Checking {len(results)} 'Pendiente' items...")
    
    count_partial = 0
    total_partial = 0
    
    for item in results:
        props = item.get("properties", {})
        
        # Name
        title_prop = props.get("Factura n°", {}).get("title", [])
        title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
        
        # Monto Asignado Total (Rollup)
        # Note: Need to handle rollup structure carefully.
        mat_prop = props.get("Monto Asignado Total", {})
        rollup = mat_prop.get("rollup", {})
        monto_asignado = 0
        
        if rollup.get("type") == "number":
            monto_asignado = rollup.get("number", 0) or 0
        # If it's another type, we assume 0 for now or handle it, 
        # but seemingly it's 'number' based on previous inspection.
        
        if monto_asignado > 0:
            count_partial += 1
            total_partial += monto_asignado
            print(f"{title[:30]:<30} | Asignado: {monto_asignado:,.2f}")
            
    print("-" * 50)
    print(f"Items with partial payments: {count_partial}")
    print(f"Total partial amount: {total_partial:,.2f}")

if __name__ == "__main__":
    check_pendiente()

