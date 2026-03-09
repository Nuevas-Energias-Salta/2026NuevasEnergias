"""
Script para actualizar CxC y CxP con las relaciones y rollups
Se ejecuta después de crear las bases de registro
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

def update_cxc_step_by_step():
    """Actualiza CxC paso a paso"""
    print("\n📤 Actualizando Cuentas por Cobrar...")
    
    # Paso 1: Crear la relación
    print("   Paso 1: Creando relación con Registro de Cobros...")
    props1 = {
        "Cobros": {
            "relation": {
                "database_id": REGISTRO_COBROS_DB_ID,
                "dual_property": {
                    "synced_property_name": "Cuenta por Cobrar"
                }
            }
        }
    }
    
    if not update_database_properties(CXC_DB_ID, props1):
        return False
    print("   ✓ Relación creada")
    time.sleep(2)
    
    # Paso 2: Crear los rollups
    print("   Paso 2: Creando rollups...")
    props2 = {
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
        }
    }
    
    if not update_database_properties(CXC_DB_ID, props2):
        return False
    print("   ✓ Rollups creados")
    time.sleep(2)
    
    # Paso 3: Crear las fórmulas
    print("   Paso 3: Creando fórmulas...")
    props3 = {
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
    
    if not update_database_properties(CXC_DB_ID, props3):
        return False
    print("   ✓ Fórmulas creadas")
    
    return True

def update_cxp_step_by_step():
    """Actualiza CxP paso a paso"""
    print("\n📥 Actualizando Cuentas por Pagar...")
    
    # Paso 1: Crear la relación
    print("   Paso 1: Creando relación con Registro de Pagos...")
    props1 = {
        "Pagos": {
            "relation": {
                "database_id": REGISTRO_PAGOS_DB_ID,
                "dual_property": {
                    "synced_property_name": "Cuenta por Pagar"
                }
            }
        }
    }
    
    if not update_database_properties(CXP_DB_ID, props1):
        return False
    print("   ✓ Relación creada")
    time.sleep(2)
    
    # Paso 2: Crear los rollups
    print("   Paso 2: Creando rollups...")
    props2 = {
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
        }
    }
    
    if not update_database_properties(CXP_DB_ID, props2):
        return False
    print("   ✓ Rollups creados")
    time.sleep(2)
    
    # Paso 3: Crear las fórmulas
    print("   Paso 3: Creando fórmulas...")
    props3 = {
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
    
    if not update_database_properties(CXP_DB_ID, props3):
        return False
    print("   ✓ Fórmulas creadas")
    
    return True

def main():
    print("=" * 60)
    print("🔗 CONFIGURANDO RELACIONES Y ROLLUPS")
    print("=" * 60)
    
    success_cxc = update_cxc_step_by_step()
    time.sleep(1)
    
    success_cxp = update_cxp_step_by_step()
    
    print("\n" + "=" * 60)
    if success_cxc and success_cxp:
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nAhora las cuentas calcularán automáticamente:")
        print("   • Monto Cobrado/Pagado (suma de registros)")
        print("   • Cantidad de Cobros/Pagos")
        print("   • Saldo Pendiente")
        print("   • Progreso (%)")
    else:
        print("❌ HUBO ERRORES EN LA CONFIGURACIÓN")
        print("=" * 60)

if __name__ == "__main__":
    main()
