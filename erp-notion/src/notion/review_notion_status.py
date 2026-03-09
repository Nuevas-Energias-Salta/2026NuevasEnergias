"""
Script para revisar el estado actual de todas las bases de datos de Notion
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import config


TOKEN = config.NOTION_TOKEN
HEADERS = config.get_notion_headers()
BASE_URL = config.NOTION_BASE_URL

DATABASES = {
    "Proyectos/Obras": "2e0c81c3-5804-8159-b677-fd8b76761e2f",
    "Cuentas por Cobrar": "2e0c81c3-5804-815a-8755-f4f254257f6a",
    "Cuentas por Pagar": "2e0c81c3-5804-8123-b1ae-d9b3579e0410",
    "Clientes": "2e0c81c3-5804-8199-8d24-ded823eae751",
    "Proveedores": "2e0c81c3-5804-81e0-94b3-e507ea920f15",
    "Registro de Cobros": "2e0c81c3-5804-810c-89e0-f99c6ed11ea5",
    "Registro de Pagos": "2e0c81c3-5804-81b1-bff1-f1ced39bf4ac",
    "Centros de Costo": "2e0c81c3-5804-81e7-80a0-dc51608efdd4",
}

def count_records(db_id):
    """Cuenta registros en una base de datos"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    total = 0
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            total += len(data.get("results", []))
            has_more = data.get("has_more", False)
            cursor = data.get("next_cursor")
        else:
            return -1
    
    return total

def get_sample_records(db_id, limit=3):
    """Obtiene registros de ejemplo"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    payload = {"page_size": limit}
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        return res.json().get("results", [])
    return []

def main():
    print("=" * 70)
    print("REVISION DE ESTADO DE NOTION")
    print("=" * 70)
    
    for db_name, db_id in DATABASES.items():
        count = count_records(db_id)
        print(f"\n{db_name}")
        print(f"   Registros: {count}")
        
        if count > 0:
            samples = get_sample_records(db_id, 2)
            for i, sample in enumerate(samples):
                try:
                    # Intentar obtener el titulo
                    props = sample.get("properties", {})
                    for key, val in props.items():
                        if val.get("type") == "title":
                            title_arr = val.get("title", [])
                            if title_arr:
                                title = title_arr[0].get("text", {}).get("content", "N/A")
                                print(f"   Ejemplo {i+1}: {title[:50]}...")
                            break
                except:
                    pass
    
    print("\n" + "=" * 70)
    print("REVISION COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
