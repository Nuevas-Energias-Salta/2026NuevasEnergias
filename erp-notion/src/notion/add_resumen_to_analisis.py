"""
Script para agregar tabla Resumen CxC dentro de Análisis CxC
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
ANALISIS_PAGE_ID = "2e3c81c3-5804-8121-842d-dff5277af513"
RESUMEN_CXC_DB_ID = "2e2c81c3-5804-8175-bd53-f36817d39dd6"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def add_resumen_to_analisis():
    """Agrega linked database de Resumen CxC a página Análisis"""
    print("Agregando tabla Resumen CxC a pagina Analisis...")
    
    url = f"{BASE_URL}/blocks/{ANALISIS_PAGE_ID}/children"
    
    payload = {
        "children": [
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📊 Resumen por Períodos"}}]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "Resumen CxC"
                }
            }
        ]
    }
    
    try:
        # Primero intentar con child_database
        res = requests.patch(url, headers=HEADERS, json=payload)
        
        if res.status_code != 200:
            # Si falla, intentar agregando la DB ID directamente
            print("Intentando método alternativo...")
            
            # La API no permite linked databases directamente
            # El usuario tendrá que agregarlo manualmente
            
            # Agregar solo instrucciones
            payload2 = {
                "children": [
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "📊 Resumen por Períodos"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "icon": {"type": "emoji", "emoji": "📋"},
                            "color": "gray_background",
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "Instrucciones: Escribir /linked y buscar 'Resumen CxC' para agregar la tabla aquí."}
                                }
                            ]
                        }
                    }
                ]
            }
            
            res2 = requests.patch(url, headers=HEADERS, json=payload2)
            if res2.status_code == 200:
                print("\nInstrucciones agregadas!")
                print("\nPara completar (manualmente en Notion):")
                print("1. Ir a pagina 'Analisis CxC'")
                print("2. Al final, escribir: /linked")
                print("3. Buscar: Resumen CxC")
                print("4. Seleccionar la base de datos")
                return True
            else:
                print(f"Error: {res2.status_code}")
                print(res2.text)
                return False
        else:
            print("Tabla agregada exitosamente!")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_resumen_to_analisis()
