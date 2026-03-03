#!/usr/bin/env python3
"""
Compare Monto vs Monto Asignado Total for Pagado items
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def compare_values():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Filter for items with Status = Pagado
    payload = {
        "page_size": 100,
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
    
    print(f"Checking {len(results)} 'Pagado' items...")
    print(f"{'Name':<30} | {'Monto':<15} | {'Monto Asignado':<15} | {'Diff':<10}")
    print("-" * 80)
    
    diff_count = 0
    total_monto = 0
    total_asignado = 0
    
    for item in results:
        props = item.get("properties", {})
        
        # Name
        title_prop = props.get("Factura n°", {}).get("title", [])
        title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
        
        # Monto
        monto = props.get("Monto", {}).get("number", 0) or 0
        total_monto += monto
        
        # Monto Asignado Total (Rollup)
        # Note: Rollup object structure can be complex.
        # Assuming it sums to a number or we need to sum specific parts
        # From previous inspect: "Monto Asignado Total": { "rollup": { "type": "number", "number": 6202156.11, "function": "sum" } }
        mat_prop = props.get("Monto Asignado Total", {}).get("rollup", {})
        monto_asignado = mat_prop.get("number", 0) or 0
        total_asignado += monto_asignado
        
        if abs(monto - monto_asignado) > 0.01:
            diff_count += 1
            print(f"{title[:30]:<30} | {monto:<15} | {monto_asignado:<15} | {monto - monto_asignado:<10.2f}")
            
    print("-" * 80)
    print(f"Total Monto:    {total_monto:,.2f}")
    print(f"Total Asignado: {total_asignado:,.2f}")
    print(f"Differences found: {diff_count}")

if __name__ == "__main__":
    compare_values()

