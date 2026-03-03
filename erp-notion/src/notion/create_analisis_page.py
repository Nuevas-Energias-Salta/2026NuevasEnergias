"""
Script para crear página 'Análisis CxC' con link a calculadora (en dos pasos)
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

config.NOTION_TOKEN
GESTION_FINANCIERA_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def create_analisis_page():
    """Crea página Análisis CxC con link"""
    print("Creando pagina 'Analisis CxC'...")
    
    # Paso 1: Crear página
    url = f"{BASE_URL}/pages"
    
    page_payload = {
        "parent": {"page_id": GESTION_FINANCIERA_ID},
        "icon": {"type": "emoji", "emoji": "📊"},
        "properties": {
            "title": [{"text": {"content": "📊 Análisis CxC"}}]
        }
    }
    
    try:
        res = requests.post(url, headers=HEADERS, json=page_payload)
        if res.status_code != 200:
            print(f"Error creando página: {res.status_code}")
            print(res.text)
            return False
        
        page_id = res.json()["id"]
        print(f"Pagina creada con ID: {page_id}")
        
        # Paso 2: Agregar contenido
        time.sleep(1)
        content_url = f"{BASE_URL}/blocks/{page_id}/children"
        
        content_payload = {
            "children": [
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "icon": {"type": "emoji", "emoji": "🧮"},
                        "color": "blue_background",
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Calculadora de Rango Personalizado\n\nPara calcular totales de un período específico: "}
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
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Nota: Después de usar la calculadora, vuelve a Resumen CxC para ver la nueva fila con los totales calculados."}
                            }
                        ]
                    }
                }
            ]
        }
        
        res2 = requests.patch(content_url, headers=HEADERS, json=content_payload)
        if res2.status_code == 200:
            print("\nContenido agregado exitosamente!")
            print("\nEn Notion:")
            print("1. Refrescar (F5)")
            print("2. Ir a 'Gestion Financiera'")
            print("3. Buscar la pagina 'Analisis CxC'")
            print("4. Abrir y hacer click en 'Abrir Calculadora CxC'")
            print(f"\nURL: {page_id}")
            return True
        else:
            print(f"Error agregando contenido: {res2.status_code}")
            print(res2.text)
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    create_analisis_page()
