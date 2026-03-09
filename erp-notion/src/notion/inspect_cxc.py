"""
Script de diagnóstico para inspeccionar las columnas de CxC y CxP
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
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def inspect_database():
    """Inspecciona la estructura de la base de datos"""
    print("🔍 Inspeccionando estructura de Cuentas por Cobrar...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code == 200:
        db = res.json()
        properties = db.get("properties", {})
        
        print("📊 Columnas encontradas:")
        print("=" * 60)
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            print(f"\n  • {prop_name}")
            print(f"    Tipo: {prop_type}")
            
            if prop_type == "formula":
                formula_type = prop_data.get("formula", {}).get("type", "unknown")
                print(f"    Fórmula tipo: {formula_type}")
            elif prop_type == "rollup":
                rollup_func = prop_data.get("rollup", {}).get("function", "unknown")
                print(f"    Rollup función: {rollup_func}")
        
        print("\n" + "=" * 60)
    else:
        print(f"❌ Error: {res.status_code}")
        print(res.text)

def inspect_first_page():
    """Inspecciona la primera página para ver cómo están los datos"""
    print("\n🔍 Inspeccionando primera cuenta...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}/query"
    payload = {"page_size": 1}
    
    res = requests.post(url, headers=HEADERS, json=payload)
    
    if res.status_code == 200:
        pages = res.json().get("results", [])
        if pages:
            page = pages[0]
            props = page["properties"]
            
            print("📋 Propiedades de la primera cuenta:")
            print("=" * 60)
            
            # Mostrar Monto
            monto_prop = props.get("Monto", {})
            print(f"\n  Monto:")
            print(f"    Tipo: {monto_prop.get('type')}")
            print(f"    Valor: {monto_prop.get('number')}") 
            
            # Mostrar Monto Cobrado
            cobrado_prop = props.get("Monto Cobrado", {})
            print(f"\n  Monto Cobrado:")
            print(f"    Tipo: {cobrado_prop.get('type')}")
            if cobrado_prop.get('type') == 'formula':
                print(f"    Formula: {cobrado_prop.get('formula')}")
            elif cobrado_prop.get('type') == 'number':
                print(f"    Valor: {cobrado_prop.get('number')}")
            else:
                print(f"    Data completa: {json.dumps(cobrado_prop, indent=2)}")
            
            # Mostrar Saldo Pendiente  
            saldo_prop = props.get("Saldo Pendiente", {})
            print(f"\n  Saldo Pendiente:")
            print(f"    Tipo: {saldo_prop.get('type')}")
            if saldo_prop.get('type') == 'formula':
                print(f"    Formula: {saldo_prop.get('formula')}")
            elif saldo_prop.get('type') == 'number':
                print(f"    Valor: {saldo_prop.get('number')}")
            else:
                print(f"    Data completa: {json.dumps(saldo_prop, indent=2)}")
            
            print("\n" + "=" * 60)
    else:
        print(f"❌ Error: {res.status_code}")

if __name__ == "__main__":
    inspect_database()
    inspect_first_page()
