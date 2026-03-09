#!/usr/bin/env python3
"""
Delete Credit Card movements uploaded today (Cleanup script)
Targets items with Concepto = "Tarjeta de Crédito" created recently.
"""

import requests
import json
import sys
import io
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

def delete_items():
    print("🔍 Buscando ítems 'Tarjeta de Crédito' para borrar...")
    
    concepts_to_delete = ["T VISA GALICIA", "T VISA BBVA", "T VISA MACRO"]
    
    for concept in concepts_to_delete:
        print(f"🔍 Buscando ítems '{concept}' para borrar...")
        
        payload = {
            "filter": {
                "property": "Concepto",
                "select": {
                    "equals": concept
                }
            }
        }
    
        deleted_count = 0
        has_more = True
        next_cursor = None
        
        batch = []
        
        while has_more:
            if next_cursor:
                payload["start_cursor"] = next_cursor
                
            response = requests.post(
                f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
                headers=HEADERS,
                json=payload
            )
            
            data = response.json()
            results = data.get("results", [])
            
            for item in results:
                batch.append(item)
                
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

        print(f"📋 Encontrados {len(batch)} ítems para eliminar de '{concept}'.")
        
        if len(batch) == 0:
            continue

        # Delete (Archive) loop
        for item in batch:
            page_id = item["id"]
            props = item.get("properties", {})
            title_prop = props.get("Factura n°", {}).get("title", [])
            title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
            
            print(f"   🗑️ Borrando: {title}...", end="")
            
            del_res = requests.patch(
                f"{NOTION_BASE_URL}/pages/{page_id}",
                headers=HEADERS,
                json={"archived": True}
            )
            
            if del_res.status_code == 200:
                print(" OK")
                deleted_count += 1
            else:
                print(f" ERROR {del_res.status_code}")

    print(f"✨ Limpieza completada.")


if __name__ == "__main__":
    delete_items()

