"""
Script para agregar la lógica de pagos parciales al ERP
Agrega columnas: Monto Cobrado/Pagado, Saldo Pendiente, y Progreso
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

# IDs de las bases de datos
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

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

def update_cuentas_por_cobrar():
    """Agrega campos de pagos parciales a Cuentas por Cobrar"""
    print("\n📤 Actualizando Cuentas por Cobrar...")
    
    new_properties = {
        "Monto Cobrado": {
            "number": {
                "format": "argentine_peso"
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
        print("   ✅ Campos agregados:")
        print("      - 💰 Monto Cobrado")
        print("      - 📊 Saldo Pendiente (fórmula)")
        print("      - 📈 Progreso (fórmula)")
        return True
    return False

def update_cuentas_por_pagar():
    """Agrega campos de pagos parciales a Cuentas por Pagar"""
    print("\n📥 Actualizando Cuentas por Pagar...")
    
    new_properties = {
        "Monto Pagado": {
            "number": {
                "format": "argentine_peso"
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
        print("   ✅ Campos agregados:")
        print("      - 💰 Monto Pagado")
        print("      - 📊 Saldo Pendiente (fórmula)")
        print("      - 📈 Progreso (fórmula)")
        return True
    return False

def main():
    print("=" * 60)
    print("💰 AGREGANDO LÓGICA DE PAGOS PARCIALES")
    print("=" * 60)
    
    success_cxc = update_cuentas_por_cobrar()
    success_cxp = update_cuentas_por_pagar()
    
    print("\n" + "=" * 60)
    if success_cxc and success_cxp:
        print("✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\n📋 Próximos pasos:")
        print("   1. Abrí Notion y revisá las nuevas columnas")
        print("   2. Podés empezar a llenar 'Monto Cobrado/Pagado'")
        print("   3. El 'Saldo Pendiente' se calculará automáticamente")
        print("   4. La barra de 'Progreso' mostrará el % pagado/cobrado")
    else:
        print("❌ HUBO ERRORES EN LA ACTUALIZACIÓN")
        print("=" * 60)

if __name__ == "__main__":
    main()
