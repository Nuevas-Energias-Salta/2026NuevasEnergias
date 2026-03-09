"""
Script para llenar datos de ejemplo de pagos parciales
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


# Configuración
config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

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

def update_page(page_id, properties):
    """Actualiza una página"""
    url = f"{BASE_URL}/pages/{page_id}"
    
    payload = {"properties": properties}
    
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.status_code == 200

def fill_cxc_partial_payments():
    """Llena datos de ejemplo de pagos parciales en CxC"""
    print("\n📤 Llenando datos de pagos parciales en Cuentas por Cobrar...")
    
    pages = query_database(CXC_DB_ID)
    
    # Definir pagos parciales para algunas cuentas
    partial_payments = {
        "Anticipo Instalación 10kWp": 2750000,  # Cobrado completo
        "Saldo Final Instalación 10kWp": 1500000,  # Cobrado parcial
        "Anticipo ACS Hotel del Sol": 800000,  # Cobrado parcial
        "Anticipo 30% Planta FV 50kWp": 7500000,  # Cobrado completo
        "Cuota 2 Planta FV 50kWp": 0,  # No cobrado (vencido)
        "Saldo Final Planta FV 50kWp": 3000000,  # Cobrado parcial
        "Honorarios Consultoría EE": 800000,  # Cobrado completo
        "Total Sistema FV 5kWp": 2800000,  # Cobrado completo
    }
    
    for page in pages:
        try:
            concepto = page["properties"]["Concepto"]["title"][0]["text"]["content"]
            
            if concepto in partial_payments:
                monto_cobrado = partial_payments[concepto]
                
                props = {
                    "Monto Cobrado": {"number": monto_cobrado}
                }
                
                if update_page(page["id"], props):
                    monto_total = page["properties"]["Monto"]["number"]
                    progreso = (monto_cobrado / monto_total * 100) if monto_total > 0 else 0
                    print(f"   ✓ {concepto}: ${monto_cobrado:,} de ${monto_total:,} ({progreso:.0f}%)")
        except:
            continue

def fill_cxp_partial_payments():
    """Llena datos de ejemplo de pagos parciales en CxP"""
    print("\n📥 Llenando datos de pagos parciales en Cuentas por Pagar...")
    
    pages = query_database(CXP_DB_ID)
    
    # Definir pagos parciales para algunas cuentas
    partial_payments = {
        "Paneles 10kWp - Casa Pérez": 2200000,  # Pagado completo
        "Inversor 10kW - Casa Pérez": 400000,  # Pagado parcial
        "Estructura Montaje - Casa Pérez": 350000,  # Pagado completo
        "Paneles 50kWp - Constructora Norte": 9500000,  # Pagado completo
        "Inversores Planta 50kWp": 0,  # No pagado (vencido)
        "Cables y Conectores Planta 50kWp": 300000,  # Pagado parcial
        "Instalación Eléctrica - Casa Pérez": 200000,  # Pagado parcial
        "Instalación Planta 50kWp - Avance": 1800000,  # Pagado completo
        "Flete Paneles a Córdoba": 280000,  # Pagado completo
        "Sueldos Diciembre 2025": 2500000,  # Pagado completo
        "Sueldos Enero 2026": 1250000,  # Pagado parcial (50%)
        "Alquiler Oficina Enero": 450000,  # Pagado completo
        "Servicios Contables": 90000,  # Pagado parcial
    }
    
    for page in pages:
        try:
            concepto = page["properties"]["Concepto"]["title"][0]["text"]["content"]
            
            if concepto in partial_payments:
                monto_pagado = partial_payments[concepto]
                
                props = {
                    "Monto Pagado": {"number": monto_pagado}
                }
                
                if update_page(page["id"], props):
                    monto_total = page["properties"]["Monto"]["number"]
                    progreso = (monto_pagado / monto_total * 100) if monto_total > 0 else 0
                    print(f"   ✓ {concepto}: ${monto_pagado:,} de ${monto_total:,} ({progreso:.0f}%)")
        except:
            continue

def main():
    print("=" * 60)
    print("💵 LLENANDO DATOS DE PAGOS PARCIALES")
    print("=" * 60)
    
    fill_cxc_partial_payments()
    fill_cxp_partial_payments()
    
    print("\n" + "=" * 60)
    print("✅ DATOS DE EJEMPLO CARGADOS")
    print("=" * 60)
    print("\nAhora podés ver en Notion:")
    print("   • Columna 'Monto Cobrado/Pagado' con valores")
    print("   • Columna 'Saldo Pendiente' calculada automáticamente")
    print("   • Columna 'Progreso' mostrando el % de avance")

if __name__ == "__main__":
    main()
