#!/usr/bin/env python3
"""
Buscar bases de datos con montos (CxC y CxP reales)
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def find_financial_databases():
    """Buscar bases de datos que contengan montos financieros"""
    print("Buscando bases de datos con información financiera...")
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    try:
        # Buscar todas las bases de datos
        search_url = f"{NOTION_BASE_URL}/search"
        search_payload = {
            "filter": {
                "property": "object",
                "value": "database"
            }
        }
        
        response = requests.post(search_url, headers=headers, json=search_payload)
        
        if response.status_code == 200:
            search_data = response.json()
            databases = search_data.get("results", [])
            
            print(f"Se encontraron {len(databases)} bases de datos:")
            
            financial_dbs = []
            
            for i, db in enumerate(databases):
                db_title = db.get("title", [{}])[0].get("text", {}).get("content", f"DB {i+1}")
                db_id = db.get("id", "")
                properties = db.get("properties", {})
                
                # Buscar propiedades financieras
                has_amount = False
                has_status = False
                financial_props = []
                
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get('type', '')
                    
                    # Buscar campos de monto
                    if prop_type == 'number' and any(keyword in prop_name.lower() for keyword in ['monto', 'amount', 'importe', 'total', 'valor', 'price']):
                        has_amount = True
                        financial_props.append(f"{prop_name} ({prop_type})")
                    
                    # Buscar campos de estado
                    if prop_type == 'select' and any(keyword in prop_name.lower() for keyword in ['estado', 'status', 'situacion', 'condicion']):
                        has_status = True
                        financial_props.append(f"{prop_name} ({prop_type})")
                
                print(f"\n{i+1}. {db_title}")
                print(f"   ID: {db_id}")
                print(f"   Propiedades: {len(properties)}")
                
                if has_amount or has_status:
                    print(f"   [FINANCIERA] Propiedades relevantes: {', '.join(financial_props)}")
                    financial_dbs.append({
                        "title": db_title,
                        "id": db_id,
                        "properties": properties,
                        "has_amount": has_amount,
                        "has_status": has_status,
                        "financial_props": financial_props
                    })
                else:
                    print(f"   No parece ser una base de datos financiera")
            
            # Guardar bases de datos financieras
            if financial_dbs:
                print(f"\n=== BASES DE DATOS FINANCIERAS ENCONTRADAS ({len(financial_dbs)}) ===")
                
                with open("financial_databases.json", "w") as f:
                    json.dump(financial_dbs, f, indent=2)
                
                for db in financial_dbs:
                    print(f"\n- {db['title']}")
                    print(f"  ID: {db['id']}")
                    print(f"  Propiedades financieras: {', '.join(db['financial_props'])}")
                
                return financial_dbs
            else:
                print("\nNo se encontraron bases de datos con propiedades financieras")
                return []
                
        else:
            print(f"Error en búsqueda: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Error buscando bases de datos: {e}")
        return []

if __name__ == "__main__":
    find_financial_databases()
