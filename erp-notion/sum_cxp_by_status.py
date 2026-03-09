#!/usr/bin/env python3
"""
Sum CxP Monto grouped by Estado
"""

import requests
import json
from collections import defaultdict

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def sum_cxp_by_status():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print(f"Calculando totales por estado en CxP...")
    
    totals = defaultdict(float)
    counts = defaultdict(int)
    
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
            
            # Estado
            status_obj = props.get("Estado", {}).get("select", {})
            status = status_obj.get("name", "Sin Estado") if status_obj else "Sin Estado"
            
            # Monto
            amount = props.get("Monto", {}).get("number", 0) or 0
            
            totals[status] += amount
            counts[status] += 1
                
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
    
    print("\nResultados:")
    print(f"{'Estado':<15} | {'Cantidad':<10} | {'Total ($)':<20}")
    print("-" * 50)
    
    grand_total = 0
    for status, total in totals.items():
        count = counts[status]
        grand_total += total
        print(f"{status:<15} | {count:<10} | ${total:,.2f}")
    
    print("-" * 50)
    print(f"{'TOTAL':<15} | {sum(counts.values()):<10} | ${grand_total:,.2f}")

if __name__ == "__main__":
    sum_cxp_by_status()

