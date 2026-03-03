"""
Script para verificar columnas de fecha en Proyectos y ver si se guardaron
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

import json

config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def check_database_properties():
    """Verifica las propiedades de la base de datos"""
    print("🔍 Inspeccionando estructura de Proyectos...\n")
    
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code == 200:
        db = res.json()
        properties = db.get("properties", {})
        
        print("📊 Columnas de FECHA encontradas:")
        print("=" * 60)
        
        date_props = []
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            if prop_type == "date":
                print(f"  ✓ {prop_name} (tipo: {prop_type})")
                date_props.append(prop_name)
        
        if not date_props:
            print("  ⚠️ No se encontraron columnas de tipo 'date'")
        
        print("\n" + "=" * 60)
        print(f"\nTotal columnas de fecha: {len(date_props)}")
        
        return date_props
    else:
        print(f"❌ Error: {res.status_code}")
        print(res.text)
        return []

def check_first_project():
    """Verifica las fechas del primer proyecto"""
    print("\n🔍 Verificando primer proyecto...\n")
    
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
    payload = {"page_size": 1}
    
    res = requests.post(url, headers=HEADERS, json=payload)
    
    if res.status_code == 200:
        pages = res.json().get("results", [])
        if pages:
            page = pages[0]
            props = page["properties"]
            
            # Mostrar nombre
            nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin nombre")
            print(f"📋 Proyecto: {nombre}\n")
            
            print("📅 Propiedades de fecha:")
            print("=" * 60)
            
            # Buscar todas las propiedades de tipo date
            for prop_name, prop_data in props.items():
                if prop_data.get("type") == "date":
                    date_val = prop_data.get("date")
                    if date_val:
                        start = date_val.get("start", "N/A")
                        end = date_val.get("end", "")
                        print(f"  • {prop_name}: {start}" + (f" → {end}" if end else ""))
                    else:
                        print(f"  • {prop_name}: (vacío)")
            
            print("=" * 60)
        else:
            print("❌ No se encontraron proyectos")
    else:
        print(f"❌ Error: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    date_props = check_database_properties()
    check_first_project()
