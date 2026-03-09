"""
Script para agregar callout con link en Gestión Financiera
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

def add_calculator_link():
    """Agrega callout con link a calculadora"""
    print("Agregando link a calculadora en Gestion Financiera...")
    
    url = f"{BASE_URL}/blocks/{PAGE_ID}/children"
    
    payload = {
        "children": [
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "📊"},
                    "color": "blue_background",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Para calcular totales de un rango personalizado de fechas: "}
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "Abrir Calculadora CxC",
                                "link": {"url": "https://administracion-ne.github.io/formulario-cxc-notion/"}
                            },
                            "annotations": {"bold": True, "color": "blue"}
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print("Link agregado exitosamente!")
            print("\nAhora en Notion:")
            print("1. Abre 'Gestion Financiera'")
            print("2. Scrollea al final")
            print("3. Veras un callout azul con el link")
            print("4. Haz click en 'Abrir Calculadora CxC'")
            return True
        else:
            print(f"Error: {res.status_code}")
            print(res.text)
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_calculator_link()
