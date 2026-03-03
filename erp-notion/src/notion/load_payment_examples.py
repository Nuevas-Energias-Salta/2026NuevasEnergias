"""
Script para cargar datos de ejemplo en los registros de cobros y pagos
Muestra cómo se registran pagos parciales individuales
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

from datetime import datetime, timedelta

# Configuración
config.NOTION_TOKEN

# IDs de las bases de datos
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"
REGISTRO_COBROS_DB_ID = "2e0c81c3-5804-810c-89e0-f99c6ed11ea5"
REGISTRO_PAGOS_DB_ID = "2e0c81c3-5804-81b1-bff1-f1ced39bf4ac"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def query_database(database_id):
    """Obtiene todas las páginas de una base de datos"""
    url = f"{BASE_URL}/databases/{database_id}/query"
    
    response = requests.post(url, headers=HEADERS, json={})
    
    if response.status_code == 200:
        return response.json()["results"]
    return []

def add_entry(database_id, properties):
    """Agrega una entrada a una base de datos"""
    url = f"{BASE_URL}/pages"
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"Error: {response.status_code} - {response.text[:200]}")
        return None

def format_date(date):
    """Formatea una fecha para Notion"""
    return date.strftime("%Y-%m-%d")

def find_cuenta_by_concepto(database_id, concepto):
    """Busca una cuenta por su concepto"""
    pages = query_database(database_id)
    
    for page in pages:
        try:
            title = page["properties"]["Concepto"]["title"][0]["text"]["content"]
            if concepto in title:
                return page["id"]
        except:
            continue
    return None

def load_cobros_ejemplo():
    """Carga registros de cobro de ejemplo"""
    print("\n📥 Cargando registros de cobro de ejemplo...")
    
    today = datetime.now()
    
    # Cuenta: "Saldo Final Instalación 10kWp" ($2.750.000)
    # Vamos a simular 2 cobros parciales
    cuenta_id = find_cuenta_by_concepto(CXC_DB_ID, "Saldo Final Instalación 10kWp")
    
    if cuenta_id:
        cobros = [
            {
                "concepto": "Cobro parcial 1 - Instalación Casa Pérez",
                "monto": 1500000,
                "fecha": today + timedelta(days=-5),
                "metodo": "Transferencia",
                "comprobante": "REC-001"
            },
            {
                "concepto": "Cobro parcial 2 - Instalación Casa Pérez",
                "monto": 1250000,
                "fecha": today + timedelta(days=2),
                "metodo": "Transferencia",
                "comprobante": "REC-002"
            }
        ]
        
        for c in cobros:
            props = {
                "Concepto": {"title": [{"text": {"content": c["concepto"]}}]},
                "Cuenta por Cobrar": {"relation": [{"id": cuenta_id}]},
                "Monto": {"number": c["monto"]},
                "Fecha Cobro": {"date": {"start": format_date(c["fecha"])}},
                "Método de Cobro": {"select": {"name": c["metodo"]}},
                "Comprobante": {"rich_text": [{"text": {"content": c["comprobante"]}}]}
            }
            
            if add_entry(REGISTRO_COBROS_DB_ID, props):
                print(f"   ✓ {c['concepto']}: ${c['monto']:,} ({c['metodo']}) - {c['comprobante']}")
    
    # Cuenta: "Saldo Final Planta FV 50kWp" ($10.000.000)
    # 3 cobros parciales
    cuenta_id = find_cuenta_by_concepto(CXC_DB_ID, "Saldo Final Planta FV 50kWp")
    
    if cuenta_id:
        cobros = [
            {
                "concepto": "Primer cobro - Planta Constructora Norte",
                "monto": 3000000,
                "fecha": today + timedelta(days=-10),
                "metodo": "Transferencia",
                "comprobante": "REC-003"
            },
            {
                "concepto": "Segundo cobro - Planta Constructora Norte",
                "monto": 3500000,
                "fecha": today + timedelta(days=-3),
                "metodo": "Cheque",
                "comprobante": "REC-004"
            },
            {
                "concepto": "Tercer cobro - Planta Constructora Norte",
                "monto": 2000000,
                "fecha": today + timedelta(days=5),
                "metodo": "Transferencia",
                "comprobante": "REC-005"
            }
        ]
        
        for c in cobros:
            props = {
                "Concepto": {"title": [{"text": {"content": c["concepto"]}}]},
                "Cuenta por Cobrar": {"relation": [{"id": cuenta_id}]},
                "Monto": {"number": c["monto"]},
                "Fecha Cobro": {"date": {"start": format_date(c["fecha"])}},
                "Método de Cobro": {"select": {"name": c["metodo"]}},
                "Comprobante": {"rich_text": [{"text": {"content": c["comprobante"]}}]}
            }
            
            if add_entry(REGISTRO_COBROS_DB_ID, props):
                print(f"   ✓ {c['concepto']}: ${c['monto']:,} ({c['metodo']}) - {c['comprobante']}")

def load_pagos_ejemplo():
    """Carga registros de pago de ejemplo"""
    print("\n📤 Cargando registros de pago de ejemplo...")
    
    today = datetime.now()
    
    # Cuenta: "Inversor 10kW - Casa Pérez" ($850.000)
    # 2 pagos parciales
    cuenta_id = find_cuenta_by_concepto(CXP_DB_ID, "Inversor 10kW - Casa Pérez")
    
    if cuenta_id:
        pagos = [
            {
                "concepto": "Pago inicial - Inversor 10kW",
                "monto": 400000,
                "fecha": today + timedelta(days=-7),
                "metodo": "Transferencia",
                "comprobante": "OP-101"
            },
            {
                "concepto": "Saldo inversor - 10kW",
                "monto": 450000,
                "fecha": today + timedelta(days=3),
                "metodo": "Transferencia",
                "comprobante": "OP-102"
            }
        ]
        
        for p in pagos:
            props = {
                "Concepto": {"title": [{"text": {"content": p["concepto"]}}]},
                "Cuenta por Pagar": {"relation": [{"id": cuenta_id}]},
                "Monto": {"number": p["monto"]},
                "Fecha Pago": {"date": {"start": format_date(p["fecha"])}},
                "Método de Pago": {"select": {"name": p["metodo"]}},
                "Comprobante": {"rich_text": [{"text": {"content": p["comprobante"]}}]}
            }
            
            if add_entry(REGISTRO_PAGOS_DB_ID, props):
                print(f"   ✓ {p['concepto']}: ${p['monto']:,} ({p['metodo']}) - {p['comprobante']}")
    
    # Cuenta: "Sueldos Enero 2026" ($2.500.000)
    # 2 pagos (anticipo + saldo)
    cuenta_id = find_cuenta_by_concepto(CXP_DB_ID, "Sueldos Enero 2026")
    
    if cuenta_id:
        pagos = [
            {
                "concepto": "Anticipo sueldos Enero",
                "monto": 1250000,
                "fecha": today + timedelta(days=-15),
                "metodo": "Transferencia",
                "comprobante": "OP-103"
            },
            {
                "concepto": "Liquidación final sueldos Enero",
                "monto": 1250000,
                "fecha": today + timedelta(days=1),
                "metodo": "Transferencia",
                "comprobante": "OP-104"
            }
        ]
        
        for p in pagos:
            props = {
                "Concepto": {"title": [{"text": {"content": p["concepto"]}}]},
                "Cuenta por Pagar": {"relation": [{"id": cuenta_id}]},
                "Monto": {"number": p["monto"]},
                "Fecha Pago": {"date": {"start": format_date(p["fecha"])}},
                "Método de Pago": {"select": {"name": p["metodo"]}},
                "Comprobante": {"rich_text": [{"text": {"content": p["comprobante"]}}]}
            }
            
            if add_entry(REGISTRO_PAGOS_DB_ID, props):
                print(f"   ✓ {p['concepto']}: ${p['monto']:,} ({p['metodo']}) - {p['comprobante']}")

def main():
    print("=" * 60)
    print("📝 CARGANDO REGISTROS DE EJEMPLO")
    print("=" * 60)
    
    load_cobros_ejemplo()
    load_pagos_ejemplo()
    
    print("\n" + "=" * 60)
    print("✅ REGISTROS CARGADOS EXITOSAMENTE")
    print("=" * 60)
    print("\nAhora podés ver en Notion:")
    print("   • Cada cobro/pago individual en los registros")
    print("   • Los totales sumados automáticamente en las cuentas")
    print("   • Saldo pendiente calculado")
    print("   • Cantidad de cobros/pagos realizados")

if __name__ == "__main__":
    main()
