"""
Script para verificar y actualizar el formato de todas las columnas de monto en CxC
para que muestren el símbolo ARS
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def check_database_properties():
    """Verifica las propiedades de la base de datos"""
    print("🔍 Verificando configuración actual...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code == 200:
        db = res.json()
        props = db.get("properties", {})
        
        print("💰 Columnas de monto:")
        print("=" * 60)
        
        for name in ["Monto", "Saldo Pendiente"]:
            if name in props:
                prop = props[name]
                prop_type = prop.get("type")
                print(f"\n{name}:")
                print(f"  Tipo: {prop_type}")
                
                if prop_type == "number":
                    num_format = prop.get("number", {}).get("format", "N/A")
                    print(f"  Formato: {num_format}")
                elif prop_type == "formula":
                    print(f"  Es fórmula (no tiene formato de número directo)")
        
        print("\n" + "=" * 60)
        return props
    else:
        print(f"❌ Error: {res.status_code}")
        return None

def update_all_currency_formats():
    """Actualiza todas las columnas de monto a formato ARS"""
    print("\n🔄 Actualizando formatos a ARS...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    
    payload = {
        "properties": {
            "Monto": {
                "number": {
                    "format": "argentine_peso"
                }
            }
        }
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print("✅ Monto actualizado a formato ARS")
            
            # Nota importante sobre Saldo Pendiente
            print("\n" + "=" * 60)
            print("ℹ️ SOBRE SALDO PENDIENTE:")
            print("=" * 60)
            print("'Saldo Pendiente' es una FÓRMULA, no un número directo.")
            print("Las fórmulas en Notion heredan el formato de las columnas")
            print("que usan en su cálculo (Monto y Monto Cobrado).")
            print("\n💡 Si 'Monto' tiene formato ARS, la fórmula debería")
            print("mostrar el resultado también en ARS con el símbolo.")
            print("\n⚠️ Si NO ves 'ARS' en Saldo Pendiente:")
            print("  1. Refrescá la página de Notion (F5)")
            print("  2. Verificá que 'Monto' y 'Monto Cobrado' tengan formato ARS")
            print("=" * 60)
            
            return True
        else:
            print(f"❌ Error: {res.status_code}")
            print(res.text)
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    current_props = check_database_properties()
    if current_props:
        update_all_currency_formats()
        print("\n✨ Proceso completado. Refrescá Notion para ver los cambios.")
