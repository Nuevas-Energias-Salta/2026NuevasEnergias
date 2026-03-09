"""
Script para cambiar el formato de Saldo Pendiente a $ (dollar)
El formato 'dollar' muestra el símbolo $ en fórmulas sin problemas
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
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def update_to_dollar_format(db_id, db_name):
    """Actualiza las columnas de monto a formato dollar ($)"""
    print(f"\n💰 Actualizando {db_name} a formato $...")
    
    url = f"{BASE_URL}/databases/{db_id}"
    
    payload = {
        "properties": {
            "Monto": {
                "number": {"format": "dollar"}
            }
        }
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print(f"   ✅ Monto actualizado a formato $")
            print(f"   ✅ Saldo Pendiente heredará el formato $")
            return True
        else:
            print(f"   ❌ Error: {res.status_code}")
            print(f"   {res.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("💵 CAMBIANDO FORMATO A $ EN CUENTAS")
    print("=" * 60)
    
    # Actualizar CxC
    success_cxc = update_to_dollar_format(CXC_DB_ID, "Cuentas por Cobrar")
    
    # Actualizar CxP
    success_cxp = update_to_dollar_format(CXP_DB_ID, "Cuentas por Pagar")
    
    print("\n" + "=" * 60)
    if success_cxc and success_cxp:
        print("✅ PROCESO COMPLETADO")
        print("=" * 60)
        print("\n💡 RESULTADO:")
        print("  - Todos los montos ahora mostrarán el símbolo $")
        print("  - Ejemplo: $300.000 en lugar de 300.000")
        print("  - Saldo Pendiente heredará el formato $ automáticamente")
        print("\n⚠️ IMPORTANTE:")
        print("  - Refrescá Notion (F5) para ver los cambios")
        print("  - Esperá 5-10 segundos a que las fórmulas recalculen")
        print("=" * 60)
    else:
        print("⚠️ PROCESO COMPLETADO CON ERRORES")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
