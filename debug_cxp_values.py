#!/usr/bin/env python3
"""
Debug CxP Values: Compare Monto vs Monto Pagado vs Estado
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

def debug_cxp_values():
    print(f"Querying CxP database...")
    
    response = requests.post(
        f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query",
        headers=headers,
        json={"page_size": 20}  # Check first 20 items
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    results = response.json().get("results", [])
    
    print(f"{'Estado':<15} | {'Monto Total':<15} | {'Monto Pagado (Rollup)':<25} | {'Monto Asignado (Rollup)':<25}")
    print("-" * 90)
    
    for item in results:
        props = item.get("properties", {})
        
        # Estado
        status_obj = props.get("Estado", {}).get("select", {})
        status = status_obj.get("name", "None") if status_obj else "None"
        
        # Monto Total
        monto = props.get("Monto", {}).get("number", 0)
        
        # Monto Pagado (Rollup)
        # Rollups can be complicated. Usually 'number' or 'array'
        monto_pagado_prop = props.get("Monto Pagado ", {}) # Note the space if present in print output earlier "Monto Pagado "
        # Check specific key from previous inspect: "Monto Pagado " : rollup
        
        monto_pagado_val = 0
        rollup = monto_pagado_prop.get("rollup", {})
        if rollup.get("type") == "number":
             monto_pagado_val = rollup.get("number", 0)
        elif rollup.get("type") == "array":
            # Sum items in array if it's an array of numbers
            items = rollup.get("array", [])
            for i in items:
                if i.get("type") == "number":
                    monto_pagado_val += i.get("number", 0)
        
        # Monto Asignado Total (Rollup)
        monto_asignado_prop = props.get("Monto Asignado Total", {})
        monto_asignado_val = 0
        rollup_asign = monto_asignado_prop.get("rollup", {})
        if rollup_asign.get("type") == "number":
             monto_asignado_val = rollup_asign.get("number", 0)

        print(f"{status:<15} | {monto:<15} | {monto_pagado_val:<25} | {monto_asignado_val:<25}")

if __name__ == "__main__":
    debug_cxp_values()

