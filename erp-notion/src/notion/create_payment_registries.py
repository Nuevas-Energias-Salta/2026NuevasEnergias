"""
Script para crear las bases de datos de Registro de Cobros y Registro de Pagos
Permite registrar cada transacción individual
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

import time

# Configuración
config.NOTION_TOKEN
PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"  # Gestion Financiera

# IDs de las bases de datos existentes
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def create_database(parent_id, title, properties, icon="📊"):
    """Crea una nueva base de datos en Notion"""
    url = f"{BASE_URL}/databases"
    
    payload = {
        "parent": {"page_id": parent_id},
        "icon": {"emoji": icon},
        "title": [{"text": {"content": title}}],
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def update_database_properties(database_id, new_properties):
    """Actualiza las propiedades de una base de datos"""
    url = f"{BASE_URL}/databases/{database_id}"
    
    payload = {
        "properties": new_properties
    }
    
    response = requests.patch(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def create_registro_cobros():
    """Crea la base de datos de Registro de Cobros"""
    print("\n📥 Creando Registro de Cobros...")
    
    properties = {
        "Concepto": {
            "title": {}
        },
        "Cuenta por Cobrar": {
            "relation": {
                "database_id": CXC_DB_ID,
                "single_property": {}
            }
        },
        "Monto": {
            "number": {
                "format": "argentine_peso"
            }
        },
        "Fecha Cobro": {
            "date": {}
        },
        "Método de Cobro": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Cheque", "color": "yellow"},
                    {"name": "Mercado Pago", "color": "purple"},
                    {"name": "Tarjeta", "color": "pink"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Comprobante": {
            "rich_text": {}
        },
        "Observaciones": {
            "rich_text": {}
        }
    }
    
    db_id = create_database(PAGE_ID, "Registro de Cobros", properties, "📥")
    
    if db_id:
        print(f"   ✅ Base de datos creada exitosamente!")
        print(f"   ID: {db_id}")
        return db_id
    return None

def create_registro_pagos():
    """Crea la base de datos de Registro de Pagos"""
    print("\n📤 Creando Registro de Pagos...")
    
    properties = {
        "Concepto": {
            "title": {}
        },
        "Cuenta por Pagar": {
            "relation": {
                "database_id": CXP_DB_ID,
                "single_property": {}
            }
        },
        "Monto": {
            "number": {
                "format": "argentine_peso"
            }
        },
        "Fecha Pago": {
            "date": {}
        },
        "Método de Pago": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Cheque", "color": "yellow"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Tarjeta", "color": "pink"},
                    {"name": "Débito Automático", "color": "orange"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Comprobante": {
            "rich_text": {}
        },
        "Observaciones": {
            "rich_text": {}
        }
    }
    
    db_id = create_database(PAGE_ID, "Registro de Pagos", properties, "📤")
    
    if db_id:
        print(f"   ✅ Base de datos creada exitosamente!")
        print(f"   ID: {db_id}")
        return db_id
    return None

def update_cuentas_por_cobrar(registro_cobros_id):
    """Actualiza CxC para usar Rollup en lugar de Number"""
    print("\n🔄 Actualizando Cuentas por Cobrar para usar Rollup...")
    
    # Primero eliminamos las propiedades antiguas
    delete_props = {
        "Monto Cobrado": None,
        "Saldo Pendiente": None,
        "Progreso": None
    }
    
    if update_database_properties(CXC_DB_ID, delete_props):
        print("   ✓ Propiedades antiguas eliminadas")
        time.sleep(2)
    
    # Ahora agregamos las nuevas con Rollup
    new_properties = {
        "Cobros": {
            "relation": {
                "database_id": registro_cobros_id,
                "dual_property": {
                    "synced_property_name": "Cuenta por Cobrar"
                }
            }
        },
        "Monto Cobrado": {
            "rollup": {
                "relation_property_name": "Cobros",
                "rollup_property_name": "Monto",
                "function": "sum"
            }
        },
        "Cantidad de Cobros": {
            "rollup": {
                "relation_property_name": "Cobros",
                "rollup_property_name": "Monto",
                "function": "count"
            }
        },
        "Saldo Pendiente": {
            "formula": {
                "expression": "prop(\"Monto\") - prop(\"Monto Cobrado\")"
            }
        },
        "Progreso": {
            "formula": {
                "expression": "if(prop(\"Monto\") > 0, prop(\"Monto Cobrado\") / prop(\"Monto\"), 0)"
            }
        }
    }
    
    if update_database_properties(CXC_DB_ID, new_properties):
        print("   ✅ Propiedades actualizadas con Rollup")
        return True
    return False

def update_cuentas_por_pagar(registro_pagos_id):
    """Actualiza CxP para usar Rollup en lugar de Number"""
    print("\n🔄 Actualizando Cuentas por Pagar para usar Rollup...")
    
    # Primero eliminamos las propiedades antiguas
    delete_props = {
        "Monto Pagado": None,
        "Saldo Pendiente": None,
        "Progreso": None
    }
    
    if update_database_properties(CXP_DB_ID, delete_props):
        print("   ✓ Propiedades antiguas eliminadas")
        time.sleep(2)
    
    # Ahora agregamos las nuevas con Rollup
    new_properties = {
        "Pagos": {
            "relation": {
                "database_id": registro_pagos_id,
                "dual_property": {
                    "synced_property_name": "Cuenta por Pagar"
                }
            }
        },
        "Monto Pagado": {
            "rollup": {
                "relation_property_name": "Pagos",
                "rollup_property_name": "Monto",
                "function": "sum"
            }
        },
        "Cantidad de Pagos": {
            "rollup": {
                "relation_property_name": "Pagos",
                "rollup_property_name": "Monto",
                "function": "count"
            }
        },
        "Saldo Pendiente": {
            "formula": {
                "expression": "prop(\"Monto\") - prop(\"Monto Pagado\")"
            }
        },
        "Progreso": {
            "formula": {
                "expression": "if(prop(\"Monto\") > 0, prop(\"Monto Pagado\") / prop(\"Monto\"), 0)"
            }
        }
    }
    
    if update_database_properties(CXP_DB_ID, new_properties):
        print("   ✅ Propiedades actualizadas con Rollup")
        return True
    return False

def main():
    print("=" * 60)
    print("📋 CREANDO SISTEMA DE REGISTRO DETALLADO DE PAGOS")
    print("=" * 60)
    
    # Crear las nuevas bases de datos
    registro_cobros_id = create_registro_cobros()
    time.sleep(1)
    
    registro_pagos_id = create_registro_pagos()
    time.sleep(1)
    
    if not registro_cobros_id or not registro_pagos_id:
        print("\n❌ Error al crear las bases de datos")
        return
    
    # Actualizar las bases existentes
    success_cxc = update_cuentas_por_cobrar(registro_cobros_id)
    time.sleep(1)
    
    success_cxp = update_cuentas_por_pagar(registro_pagos_id)
    
    print("\n" + "=" * 60)
    if success_cxc and success_cxp:
        print("✅ SISTEMA DE REGISTRO CREADO EXITOSAMENTE")
        print("=" * 60)
        print("\nBases de datos creadas:")
        print(f"   📥 Registro de Cobros: {registro_cobros_id}")
        print(f"   📤 Registro de Pagos: {registro_pagos_id}")
        print("\nAhora podés:")
        print("   1. Registrar cada cobro individual en 'Registro de Cobros'")
        print("   2. Registrar cada pago individual en 'Registro de Pagos'")
        print("   3. Ver el total sumado automáticamente en las cuentas")
        
        # Guardar los IDs para uso posterior
        with open("database_ids.txt", "a", encoding="utf-8") as f:
            f.write(f"\nREGISTRO_COBROS_DB_ID = {registro_cobros_id}")
            f.write(f"\nREGISTRO_PAGOS_DB_ID = {registro_pagos_id}")
    else:
        print("❌ HUBO ERRORES EN LA ACTUALIZACIÓN")
        print("=" * 60)

if __name__ == "__main__":
    main()
