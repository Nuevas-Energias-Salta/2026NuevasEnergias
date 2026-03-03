"""
Script para LIMPIAR COMPLETAMENTE todas las bases de datos de Notion
⚠️ ADVERTENCIA: Esto borrará TODOS los datos - SIN CONFIRMACIÓN
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

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

# IDs de las bases de datos
DATABASES = {
    "Proyectos/Obras": "2e0c81c3-5804-8159-b677-fd8b76761e2f",
    "Cuentas por Cobrar": "2e0c81c3-5804-815a-8755-f4f254257f6a",
    "Cuentas por Pagar": "2e0c81c3-5804-8145-ad63-d56e73de4a16",
    "Clientes": "2e0c81c3-5804-8199-8d24-ded823eae751",
    "Proveedores": "2e0c81c3-5804-81fd-a1ca-e3fabd86b0df",
    "Registro de Cobros": "2e0c81c3-5804-8128-abd5-fb0a84cf2a8a",
    "Registro de Pagos": "2e0c81c3-5804-8103-8e58-e5c012c8d40c",
}

def get_all_pages(db_id):
    """Obtiene todas las páginas de una base de datos"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    all_pages = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            all_pages.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            cursor = data.get("next_cursor")
        else:
            break
    
    return all_pages

def delete_page(page_id):
    """Elimina una página (archivo)"""
    url = f"{BASE_URL}/blocks/{page_id}"
    res = requests.delete(url, headers=HEADERS)
    return res.status_code == 200

def clean_database(db_name, db_id):
    """Limpia completamente una base de datos"""
    print(f"\nLimpiando: {db_name}")
    
    pages = get_all_pages(db_id)
    total = len(pages)
    
    print(f"   Encontradas {total} entradas")
    
    if total == 0:
        print("   Ya esta vacia")
        return
    
    deleted = 0
    for i, page in enumerate(pages):
        if delete_page(page["id"]):
            deleted += 1
            if (i + 1) % 10 == 0:
                print(f"   Eliminadas: {i + 1}/{total}")
    
    print(f"   Eliminadas: {deleted}/{total}")

def main():
    print("=" * 60)
    print("LIMPIEZA COMPLETA DE BASES DE DATOS")
    print("=" * 60)
    
    print("\nIniciando limpieza...")
    
    for db_name, db_id in DATABASES.items():
        clean_database(db_name, db_id)
    
    print("\n" + "=" * 60)
    print("LIMPIEZA COMPLETADA")
    print("=" * 60)
    print("\nTodas las bases de datos estan vacias.")
    print("Ahora ejecuta:")
    print("  1. python import_trello.py")
    print("  2. python auto_generate_cxc_improved.py")

if __name__ == "__main__":
    main()
