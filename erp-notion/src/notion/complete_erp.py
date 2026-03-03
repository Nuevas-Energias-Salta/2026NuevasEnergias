"""
Script para crear las bases de datos faltantes del ERP en Notion
Crea: Proyectos/Obras, Cuentas por Cobrar, Cuentas por Pagar
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import config

import time

# Configuración
TOKEN = config.NOTION_TOKEN
PAGE_ID = config.NOTION_PAGE_ID
HEADERS = config.get_notion_headers()
BASE_URL = config.NOTION_BASE_URL

# IDs de las bases de datos ya creadas
CENTROS_DB_ID = config.CENTROS_DB_ID
CLIENTES_DB_ID = config.CLIENTES_DB_ID
PROVEEDORES_DB_ID = config.PROVEEDORES_DB_ID

def create_database(parent_id, title, properties, icon="📊"):
    """Crea una base de datos en Notion"""
    url = f"{BASE_URL}/databases"
    
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "icon": {"type": "emoji", "emoji": icon},
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Base de datos '{title}' creada exitosamente!")
        return response.json()
    else:
        print(f"❌ Error creando '{title}': {response.status_code}")
        print(response.text)
        return None

# ============================================
# PROYECTOS/OBRAS
# ============================================
def create_proyectos():
    print("\n🏗️ Creando base de datos: Proyectos/Obras...")
    
    properties = {
        "Nombre": {"title": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Cotización", "color": "gray"},
                    {"name": "Aprobado", "color": "blue"},
                    {"name": "En Ejecución", "color": "yellow"},
                    {"name": "Finalizado", "color": "green"},
                    {"name": "Cancelado", "color": "red"}
                ]
            }
        },
        "Monto Contrato": {"number": {"format": "argentine_peso"}},
        "Fecha Inicio": {"date": {}},
        "Fecha Fin Estimada": {"date": {}},
        "Fecha Fin Real": {"date": {}},
        "Potencia kWp": {"number": {"format": "number"}},
        "Ubicación": {"rich_text": {}},
        "Referencia Trello": {"url": {}},
        "Notas": {"rich_text": {}},
        "Cliente": {"relation": {"database_id": CLIENTES_DB_ID, "single_property": {}}},
        "Centro de Costo": {"relation": {"database_id": CENTROS_DB_ID, "single_property": {}}}
    }
    
    db = create_database(PAGE_ID, "Proyectos/Obras", properties, "🏗️")
    return db["id"] if db else None

# ============================================
# CUENTAS POR COBRAR
# ============================================
def create_cuentas_por_cobrar(proyectos_db_id):
    print("\n📤 Creando base de datos: Cuentas por Cobrar...")
    
    properties = {
        "Concepto": {"title": {}},
        "Tipo Cobro": {
            "select": {
                "options": [
                    {"name": "Anticipo", "color": "blue"},
                    {"name": "Cuota", "color": "purple"},
                    {"name": "Saldo Final", "color": "green"},
                    {"name": "Abono Mensual", "color": "orange"},
                    {"name": "Honorarios", "color": "pink"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Número Factura": {"rich_text": {}},
        "Monto": {"number": {"format": "argentine_peso"}},
        "Fecha Emisión": {"date": {}},
        "Fecha Vencimiento": {"date": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Pendiente", "color": "yellow"},
                    {"name": "Cobrado", "color": "green"},
                    {"name": "Vencido", "color": "red"},
                    {"name": "Anulado", "color": "gray"}
                ]
            }
        },
        "Fecha Cobro": {"date": {}},
        "Método Pago": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Cheque", "color": "orange"},
                    {"name": "Mercado Pago", "color": "purple"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Notas": {"rich_text": {}},
        "Cliente": {"relation": {"database_id": CLIENTES_DB_ID, "single_property": {}}},
        "Centro de Costo": {"relation": {"database_id": CENTROS_DB_ID, "single_property": {}}}
    }
    
    if proyectos_db_id:
        properties["Proyecto"] = {"relation": {"database_id": proyectos_db_id, "single_property": {}}}
    
    db = create_database(PAGE_ID, "Cuentas por Cobrar", properties, "📤")
    return db["id"] if db else None

# ============================================
# CUENTAS POR PAGAR
# ============================================
def create_cuentas_por_pagar(proyectos_db_id):
    print("\n📥 Creando base de datos: Cuentas por Pagar...")
    
    properties = {
        "Concepto": {"title": {}},
        "Categoría": {
            "select": {
                "options": [
                    {"name": "Materiales", "color": "yellow"},
                    {"name": "Mano de Obra", "color": "blue"},
                    {"name": "Sueldos", "color": "green"},
                    {"name": "Transporte", "color": "purple"},
                    {"name": "Servicios", "color": "pink"},
                    {"name": "Alquiler", "color": "orange"},
                    {"name": "Impuestos", "color": "red"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Número Factura": {"rich_text": {}},
        "Monto": {"number": {"format": "argentine_peso"}},
        "Fecha Factura": {"date": {}},
        "Fecha Vencimiento": {"date": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Pendiente", "color": "yellow"},
                    {"name": "Pagado", "color": "green"},
                    {"name": "Vencido", "color": "red"},
                    {"name": "Anulado", "color": "gray"}
                ]
            }
        },
        "Fecha Pago": {"date": {}},
        "Método Pago": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Cheque", "color": "orange"},
                    {"name": "Débito Automático", "color": "purple"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Notas": {"rich_text": {}},
        "Proveedor": {"relation": {"database_id": PROVEEDORES_DB_ID, "single_property": {}}},
        "Centro de Costo": {"relation": {"database_id": CENTROS_DB_ID, "single_property": {}}}
    }
    
    if proyectos_db_id:
        properties["Proyecto"] = {"relation": {"database_id": proyectos_db_id, "single_property": {}}}
    
    db = create_database(PAGE_ID, "Cuentas por Pagar", properties, "📥")
    return db["id"] if db else None

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 50)
    print("🚀 COMPLETANDO ERP EN NOTION")
    print("=" * 50)
    print(f"Página destino: {PAGE_ID}")
    print(f"\nUsando bases de datos existentes:")
    print(f"  🏷️ Centros de Costo: {CENTROS_DB_ID}")
    print(f"  👥 Clientes: {CLIENTES_DB_ID}")
    print(f"  🏢 Proveedores: {PROVEEDORES_DB_ID}")
    
    # Crear las 3 bases de datos faltantes
    proyectos_db_id = create_proyectos()
    time.sleep(1)
    
    cxc_db_id = create_cuentas_por_cobrar(proyectos_db_id)
    time.sleep(1)
    
    cxp_db_id = create_cuentas_por_pagar(proyectos_db_id)
    
    print("\n" + "=" * 50)
    print("✅ PROCESO COMPLETADO")
    print("=" * 50)
    print("\nNuevas bases de datos creadas:")
    print(f"  🏗️ Proyectos/Obras: {proyectos_db_id}")
    print(f"  📤 Cuentas por Cobrar: {cxc_db_id}")
    print(f"  📥 Cuentas por Pagar: {cxp_db_id}")
    print("\n¡Revisá tu Notion para ver las bases de datos!")

if __name__ == "__main__":
    main()
