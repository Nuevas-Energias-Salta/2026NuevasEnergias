#!/usr/bin/env python3
"""
Update CxC Status to 'Cobrado' if Balance is 0
Logic: If (Monto Base - Monto Cobrado Base) <= 0 and Status != Cobrado -> Update to Cobrado
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

def update_cxc_status():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print(f"Scanning CxC for items to update...")
    
    # We fetch specifically 'Pendiente' items as requested
    payload = {
        "page_size": 100,
        "filter": {
            "property": "Estado",
            "select": {
                "equals": "Pendiente"
            }
        }
    }
    
    has_more = True
    next_cursor = None
    updated_count = 0
    
    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor
            
        response = requests.post(
            f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query",
            headers=headers,
            json=payload
        )
        
        data = response.json()
        results = data.get("results", [])
        
        for item in results:
            props = item.get("properties", {})
            page_id = item.get("id")
            
            # 1. Get Monto Base
            monto_base = props.get("Monto Base", {}).get("number", 0) or 0
            
            # 2. Get Monto Cobrado Base (Rollup)
            mcb_prop = props.get("Monto Cobrado Base", {})
            rollup = mcb_prop.get("rollup", {})
            monto_cobrado = 0
            
            if rollup.get("type") == "number":
                monto_cobrado = rollup.get("number", 0) or 0
            
            # 3. Calculate Balance
            balance = monto_base - monto_cobrado
            
            # 4. Check Title for logging
            title_prop = props.get("Concepto", {}).get("title", [])
            title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
            
            # 5. Update if Balance <= 0 (allow small float error)
            if balance <= 1.0: 
                print(f"Updating '{title}' (Balance: {balance}) -> Cobrado")
                
                update_payload = {
                    "properties": {
                        "Estado": {
                            "select": {
                                "name": "Cobrado"
                            }
                        }
                    }
                }
                
                upd_response = requests.patch(
                    f"{NOTION_BASE_URL}/pages/{page_id}",
                    headers=headers,
                    json=update_payload
                )
                
                if upd_response.status_code == 200:
                    updated_count += 1
                else:
                    print(f"Failed to update {page_id}: {upd_response.status_code}")
                    
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
        
    print(f"Total items updated: {updated_count}")

if __name__ == "__main__":
    update_cxc_status()

