#!/usr/bin/env python3
"""
Probar conexión directa con Notion API - sin emojis
"""

import requests
import json

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def test_notion_connection():
    """Probar conexión con Notion"""
    try:
        print("Probando conexión con Notion API...")
        
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        
        # Probar obtener información del usuario
        print("1. Probando obtener información del usuario...")
        user_url = f"{NOTION_BASE_URL}/users/me"
        response = requests.get(user_url, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("   [OK] Conexión exitosa!")
            print(f"   Usuario: {user_data.get('results', [{}])[0].get('name', 'Unknown')}")
            
            # Probar listar bases de datos
            print("\n2. Probando listar bases de datos...")
            search_url = f"{NOTION_BASE_URL}/search"
            search_payload = {
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }
            
            search_response = requests.post(search_url, headers=headers, json=search_payload)
            print(f"   Status Code: {search_response.status_code}")
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                databases = search_data.get("results", [])
                print(f"   [OK] Se encontraron {len(databases)} bases de datos:")
                
                for i, db in enumerate(databases[:5]):  # Mostrar primeras 5
                    db_title = db.get("title", [{}])[0].get("text", {}).get("content", "Sin título")
                    db_id = db.get("id", "")
                    print(f"   {i+1}. {db_title} (ID: {db_id[:8]}...)")
                
                # Guardar información para el dashboard
                db_info = {
                    "databases": [],
                    "connection": "success"
                }
                
                for db in databases:
                    db_title = db.get("title", [{}])[0].get("text", {}).get("content", "Sin título")
                    db_id = db.get("id", "")
                    db_info["databases"].append({
                        "title": db_title,
                        "id": db_id
                    })
                
                with open("notion_databases.json", "w") as f:
                    json.dump(db_info, f, indent=2)
                
                print(f"\n   Información guardada en notion_databases.json")
                return True
            else:
                print(f"   [ERROR] Error en búsqueda: {search_response.text}")
                return False
        else:
            print(f"   [ERROR] Error en autenticación: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_notion_connection()
