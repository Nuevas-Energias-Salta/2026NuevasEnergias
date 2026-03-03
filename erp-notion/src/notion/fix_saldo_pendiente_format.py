"""
Script para actualizar el formato de Saldo Pendiente a ARS en CxC
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

def update_saldo_pendiente_format():
    """Actualiza el formato de Saldo Pendiente a ARS"""
    print("🔄 Actualizando formato de Saldo Pendiente a ARS...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    
    # Actualizar la propiedad para que use formato argentino
    payload = {
        "properties": {
            "Saldo Pendiente": {
                "formula": {
                    "expression": "prop(\"Monto\") - prop(\"Monto Cobrado\")"
                },
                "number": {
                    "format": "argentine_peso"
                }
            }
        }
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print("✅ Formato actualizado a ARS exitosamente!")
            return True
        else:
            print(f"❌ Error {res.status_code}")
            print(res.text)
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    update_saldo_pendiente_format()
