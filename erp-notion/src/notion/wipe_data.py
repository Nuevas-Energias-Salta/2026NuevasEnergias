"""
Script para borrar TODOS los datos de las bases de datos del ERP.
ADVERTENCIA: Esto eliminará permanentemente los datos.
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

# IDs de bases de datos a limpiar
DATABASES = {
    "Proyectos/Obras": "2e0c81c3-5804-8159-b677-fd8b76761e2f",
    "Clientes": "2e0c81c3-5804-8199-8d24-ded823eae751",
    "Cuentas por Cobrar": "2e0c81c3-5804-815a-8755-f4f254257f6a",
    "Cuentas por Pagar": "2e0c81c3-5804-8123-b1ae-d9b3579e0410",
    "Registro de Cobros": "2e0c81c3-5804-810c-89e0-f99c6ed11ea5",
    "Registro de Pagos": "2e0c81c3-5804-81b1-bff1-f1ced39bf4ac",
    # Proveedores y Centros de Costo NO se borran por defecto para mantener estructura básica
    # "Proveedores": "2e0c81c3-5804-81e0-94b3-e507ea920f15", 
}

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def get_all_pages(database_id):
    url = f"{BASE_URL}/databases/{database_id}/query"
    pages = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {}
        if cursor: payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code != 200:
            print(f"Error query: {res.text}")
            break
            
        data = res.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
        
    return pages

def delete_page(page_id):
    url = f"{BASE_URL}/pages/{page_id}"
    payload = {"archived": True}
    res = requests.patch(url, headers=HEADERS, json=payload)
    return res.status_code == 200

def wipe_all():
    print("⚠️  INICIANDO BORRADO DE DATOS")
    print("=" * 60)
    
    for name, db_id in DATABASES.items():
        print(f"\n🗑️  Limpiando: {name}...")
        pages = get_all_pages(db_id)
        print(f"    Encontrados {len(pages)} registros.")
        
        count = 0
        for page in pages:
            if delete_page(page["id"]):
                count += 1
                if count % 10 == 0: print(f"    ...borrados {count}")
            else:
                print("    Error borrando página")
            time.sleep(0.1) # Rate limit friendly
            
        print(f"    ✅ {count} registros eliminados.")

    print("\n" + "=" * 60)
    print("✨ Base de datos limpia y lista para importación.")

if __name__ == "__main__":
    wipe_all()
