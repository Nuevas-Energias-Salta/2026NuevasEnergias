"""
Script para agregar botón de sincronización Trello en Notion
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
GESTION_FINANCIERA_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def add_sync_button():
    """Agrega callout con link para sincronizar Trello"""
    print("Agregando boton de sincronizacion Trello...")
    
    url = f"{BASE_URL}/blocks/{GESTION_FINANCIERA_ID}/children"
    
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
                    "icon": {"type": "emoji", "emoji": "🔄"},
                    "color": "green_background",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Sincronizar Trello\n\nPara importar nuevas tarjetas de Trello a Notion: "}
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "Sincronizar Ahora",
                                "link": {"url": "https://n8n.odontia.tech/webhook/sync-trello"}
                            },
                            "annotations": {"bold": True, "color": "green"}
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print("Boton agregado exitosamente!")
            print("\nEn Notion:")
            print("1. Ir a 'Gestion Financiera'")
            print("2. Veras un callout verde 'Sincronizar Trello'")
            print("3. Click en 'Sincronizar Ahora' para importar tarjetas")
            return True
        else:
            print(f"Error: {res.status_code}")
            print(res.text)
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_sync_button()
