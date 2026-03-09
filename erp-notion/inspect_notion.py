#!/usr/bin/env python3
"""
Inspeccionar estructura de bases de datos de Notion
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs de bases de datos
CXP_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"
CXC_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"

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
            print(f"Título: {db_info.get('title', [{}])[0].get('text', {}).get('content', 'Sin título')}")
            
            # Mostrar propiedades
            properties = db_info.get('properties', {})
            print(f"Propiedades ({len(properties)}):")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                print(f"  - {prop_name}: {prop_type}")
            
            # Obtener algunos registros de ejemplo
            print(f"\nRegistros de ejemplo:")
            query_url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
            query_response = requests.post(query_url, headers=headers, json={"page_size": 3})
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                results = query_data.get("results", [])
                
                for i, result in enumerate(results):
                    print(f"\n  Registro {i+1}:")
                    props = result.get("properties", {})
                    
                    for prop_name, prop_value in props.items():
                        if prop_name in ['Monto', 'Estado', 'Status', 'Amount', 'Importe']:
                            print(f"    {prop_name}: {prop_value}")
                            
                            # Si es un número, mostrar el valor
                            if prop_value.get('type') == 'number':
                                number = prop_value.get('number', 0)
                                print(f"      Valor numérico: {number}")
                            
                            # Si es un select, mostrar las opciones
                            elif prop_value.get('type') == 'select':
                                select_info = prop_value.get('select', {})
                                if select_info:
                                    print(f"      Opción seleccionada: {select_info.get('name', 'N/A')}")
                                else:
                                    print(f"      Sin selección")
            else:
                print(f"Error consultando registros: {query_response.status_code}")
                
        else:
            print(f"Error obteniendo info de DB: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error inspeccionando {db_name}: {e}")

if __name__ == "__main__":
    inspect_database(CXC_DB_ID, "Cuentas por Cobrar")
    inspect_database(CXP_DB_ID, "Cuentas por Pagar")
    inspect_database(CENTROS_DB_ID, "Centros/Proyectos")
