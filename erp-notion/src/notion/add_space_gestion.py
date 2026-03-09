"""
Script para agregar un bloque de texto en Gestión Financiera
donde el usuario podrá escribir /linked
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
PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"  # Gestión Financiera

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def add_text_block():
    """Agrega un bloque de texto al final de Gestión Financiera"""
    print("📝 Agregando espacio en Gestión Financiera...")
    
    url = f"{BASE_URL}/blocks/{PAGE_ID}/children"
    
    payload = {
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📅 Análisis por Rango de Fechas"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Borrar este texto y escribir /linked para crear vista de Cuentas por Cobrar"}}]
                }
            }
        ]
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print("✅ Espacio creado exitosamente")
            print("\n💡 Ahora en Notion:")
            print("   1. Ir a 'Gestión Financiera'")
            print("   2. Al final verás un texto que dice 'Borrar este texto...'")
            print("   3. Borrarlo y escribir /linked")
            print("   4. Seleccionar 'Cuentas por Cobrar'")
            return True
        else:
            print(f"❌ Error: {res.status_code}")
            print(res.text)
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_text_block()
