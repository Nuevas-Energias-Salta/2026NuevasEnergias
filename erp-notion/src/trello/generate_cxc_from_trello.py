"""
Script para generar Cuentas por Cobrar desde proyectos activos de Trello
Listas 1 y 2 = Proyectos con monto pendiente de cobrar
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import time
from datetime import datetime, timedelta
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


# Credenciales Trello
config.TRELLO_API_KEY
config.TRELLO_TOKEN
BOARD_ID = "612f6ea39c967b8bef5c2186"

# Credenciales Notion
config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

HEADERS_NOTION = {
    f"Bearer {config.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Listas de Trello que representan proyectos activos (1 y 2)
LISTAS_ACTIVAS = [
    "1-Proyecto nuevo (Cobrado anticipo)/ PostVenta Activado",
    "2-Comprar materiales y productos",
    "2 - Obra",
    "2.1 - No Conforme/Postventa"
]

def get_trello_lists():
    """Obtiene las listas del board con sus IDs"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    params = config.get_trello_params()
    res = requests.get(url, params=params)
    return {l['id']: l['name'] for l in res.json()}

def get_trello_cards_with_custom_fields():
    """Obtiene tarjetas con custom fields"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    params = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'customFieldItems': 'true',
        'fields': 'name,idList'
    }
    return requests.get(url, params=params).json()

def get_custom_field_definitions():
    """Obtiene definiciones de custom fields"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/customFields"
    params = config.get_trello_params()
    cf_defs = requests.get(url, params=params).json()
    return {cf['id']: cf['name'] for cf in cf_defs}

def extract_monto(card, cf_names):
    """Extrae el monto de la tarjeta"""
    for cf in card.get('customFieldItems', []):
        field_name = cf_names.get(cf['idCustomField'], '')
        if 'monto' in field_name.lower():
            val = cf.get('value', {})
            if 'number' in val:
                try:
                    return float(val['number'])
                except:
                    pass
    return 0

def find_proyecto_in_notion(nombre):
    """Busca un proyecto en Notion por nombre"""
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Nombre",
            "title": {"equals": nombre}
        }
    }
    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    if res.status_code == 200:
        results = res.json().get("results", [])
        if results:
            return results[0]["id"]
    return None

def cxc_exists(proyecto_id):
    """Verifica si ya existe una CxC para el proyecto"""
    url = f"https://api.notion.com/v1/databases/{CXC_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Proyecto",
            "relation": {"contains": proyecto_id}
        }
    }
    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    if res.status_code == 200:
        return len(res.json().get("results", [])) > 0
    return False

def create_cxc(proyecto_id, nombre, monto):
    """Crea una Cuenta por Cobrar en Notion"""
    url = "https://api.notion.com/v1/pages"
    
    # Fecha de vencimiento: 30 dias desde hoy
    fecha_venc = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    payload = {
        "parent": {"database_id": CXC_DB_ID},
        "properties": {
            "Concepto": {
                "title": [{"text": {"content": f"CxC - {nombre[:40]}"}}]
            },
            "Proyecto": {
                "relation": [{"id": proyecto_id}]
            },
            "Monto Total": {
                "number": monto
            },
            "Monto Cobrado": {
                "number": 0
            },
            "Estado": {
                "select": {"name": "Pendiente"}
            },
            "Fecha Vencimiento": {
                "date": {"start": fecha_venc}
            }
        }
    }
    
    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    return res.status_code == 200

def main():
    print("=" * 70)
    print("GENERACION DE CUENTAS POR COBRAR DESDE TRELLO")
    print("=" * 70)
    print()
    
    # Obtener datos de Trello
    print("Obteniendo datos de Trello...")
    lists_map = get_trello_lists()
    cards = get_trello_cards_with_custom_fields()
    cf_names = get_custom_field_definitions()
    
    # Identificar IDs de listas activas
    listas_activas_ids = []
    for list_id, list_name in lists_map.items():
        for activa in LISTAS_ACTIVAS:
            if activa.lower() in list_name.lower() or list_name.lower() in activa.lower():
                listas_activas_ids.append(list_id)
                print(f"   Lista activa: {list_name}")
    
    print(f"\nTarjetas totales en Trello: {len(cards)}")
    
    # Filtrar tarjetas en listas activas
    tarjetas_activas = [c for c in cards if c['idList'] in listas_activas_ids]
    print(f"Tarjetas en listas 1 y 2: {len(tarjetas_activas)}")
    
    # Procesar cada tarjeta
    creadas = 0
    saltadas = 0
    sin_monto = 0
    sin_proyecto = 0
    
    print("\nProcesando tarjetas...")
    
    for card in tarjetas_activas:
        nombre = card['name']
        monto = extract_monto(card, cf_names)
        
        # Verificar que tenga monto
        if monto <= 0:
            sin_monto += 1
            continue
        
        # Buscar proyecto en Notion
        proyecto_id = find_proyecto_in_notion(nombre)
        if not proyecto_id:
            print(f"   Proyecto no encontrado: {nombre[:40]}")
            sin_proyecto += 1
            continue
        
        # Verificar si ya existe CxC
        if cxc_exists(proyecto_id):
            saltadas += 1
            continue
        
        # Crear CxC
        if create_cxc(proyecto_id, nombre, monto):
            print(f"   CxC creada: {nombre[:40]} - ${monto:,.0f}")
            creadas += 1
        
        time.sleep(0.3)  # Rate limiting
    
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"   CxC creadas: {creadas}")
    print(f"   Ya existian: {saltadas}")
    print(f"   Sin monto: {sin_monto}")
    print(f"   Proyecto no encontrado: {sin_proyecto}")

if __name__ == "__main__":
    main()
