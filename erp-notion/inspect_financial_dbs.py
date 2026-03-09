#!/usr/bin/env python3
"""
Inspeccionar estructura de bases de datos financieras (IDs de dashboard_server_correct.py)
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs de bases de datos (de dashboard_server_correct.py)
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"  # Posible CxC Real
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"  # Posible CxP Real

def inspect_database(db_id, db_name):
    """Inspeccionar estructura de una base de datos"""
    print(f"\n=== Inspeccionando {db_name} ===")
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    try:
        # Obtener información de la base de datos
        db_url = f"{NOTION_BASE_URL}/databases/{db_id}"
        response = requests.get(db_url, headers=headers)
        
        if response.status_code == 200:
            db_info = response.json()
            title = db_info.get('title', [{}])
            title_text = title[0].get('text', {}).get('content', 'Sin título') if title else 'Sin título'
            print(f"Título: {title_text}")
            
            # Mostrar propiedades
            properties = db_info.get('properties', {})
            print(f"Propiedades ({len(properties)}):")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                print(f"  - {prop_name}: {prop_type}")
            
            # Obtener algunos registros de ejemplo
            print(f"\nRegistros de ejemplo (buscando campos de monto):")
            query_url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
            query_response = requests.post(query_url, headers=headers, json={"page_size": 1})
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                results = query_data.get("results", [])
                
                if results:
                    result = results[0]
                    props = result.get("properties", {})
                    
                    found_amount = False
                    for prop_name, prop_value in props.items():
                        # Mostrar valores de campos que parecen montos o estados
                        if any(x in prop_name.lower() for x in ['monto', 'amount', 'importe', 'balance', 'total', 'precio', 'estado', 'status']):
                            print(f"    {prop_name} ({prop_value.get('type')}): {json.dumps(prop_value.get(prop_value.get('type')), indent=2)}")
                            found_amount = True
                    
                    if not found_amount:
                        print("    No se encontraron campos de monto obvios en el primer registro.")
                else:
                    print("    No hay registros.")
            else:
                print(f"Error consultando registros: {query_response.status_code}")
                
        else:
            print(f"Error obteniendo info de DB ({db_id}): {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error inspeccionando {db_name}: {e}")

if __name__ == "__main__":
    inspect_database(CXC_DB_ID, "Posible CxC (Invoices)")
    inspect_database(CXP_DB_ID, "Posible CxP (Expenses)")

