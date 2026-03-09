"""
Script de Integración Trello -> Notion
Importa tarjetas del tablero 'Kanban Nuevas Energías' a la base de datos de Proyectos en Notion.
Realiza mapeo de estados, creación de clientes y vinculación de centros de costo.
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import json
import time
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---

# Credenciales Trello
config.TRELLO_API_KEY
config.TRELLO_TOKEN
BOARD_ID = "612f6ea39c967b8bef5c2186"

# Credenciales Notion
config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CLIENTES_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"

HEADERS_NOTION = {
    f"Bearer {config.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# --- MAPEOS ---

# Mapeo de Estados (Lista Trello -> Estado Notion)
ESTADOS_MAP = {
    "1-Proyecto nuevo (Cobrado anticipo)/ PostVenta Activado": "Aprobado",
    "2-Comprar materiales y productos": "En Ejecución", # Asumimos paso previo a obra
    "2 - Obra": "En Ejecución",
    "2.1 - No Conforme/Postventa": "En Ejecución", # Ojo, revisar si Postventa es un estado
    "3 - Fin": "Finalizado",
    "4 - Freezer": "Cancelado" 
}

# Mapeo de Etiquetas a Centros de Costo (Nombre Etiqueta Trello "in" -> ID Notion calculado dinámicamente)
def get_cc_mapping():
    # Obtener centros de costo de Notion para mapear dinámicamente
    url = f"https://api.notion.com/v1/databases/{CENTROS_DB_ID}/query"
    res = requests.post(url, headers=HEADERS_NOTION, json={})
    centers = res.json().get("results", [])
    
    mapping = {}
    for c in centers:
        try:
            name = c["properties"]["Centro de Costo"]["title"][0]["text"]["content"]
            c_id = c["id"]
            # Mapeos simples basados en palabras clave
            if "Solar" in name: mapping["Solar"] = c_id
            if "Piletas" in name: mapping["Climat"] = c_id
            if "ACS" in name: mapping["ACS"] = c_id
        except:
            pass
    return mapping

# --- FUNCIONES ---

def get_trello_cards():
    """Obtiene todas las tarjetas del tablero con sus custom fields"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'customFieldItems': 'true',
        'fields': 'name,idList,desc,labels,dateLastActivity'
    }
    return requests.get(url, params=query).json()

def get_trello_lists():
    """Obtiene mapas de ID Lista -> Nombre Lista"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    query = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}
    lists = requests.get(url, params=query).json()
    return {l['id']: l['name'] for l in lists}

def find_or_create_client(name, email, phone):
    """Busca un cliente por nombre, si no existe lo crea"""
    if not name: return None
    
    # Buscar
    query_payload = {
        "filter": {
            "property": "Nombre",
            "title": {"equals": name}
        }
    }
    url_query = f"https://api.notion.com/v1/databases/{CLIENTES_DB_ID}/query"
    res = requests.post(url_query, headers=HEADERS_NOTION, json=query_payload)
    results = res.json().get("results", [])
    
    if results:
        return results[0]["id"]
    
    # Crear
    print(f"      👤 Creando nuevo cliente: {name}")
    create_payload = {
        "parent": {"database_id": CLIENTES_DB_ID},
        "properties": {
            "Nombre": {"title": [{"text": {"content": name}}]}
        }
    }
    if email:
        create_payload["properties"]["Email"] = {"email": email}
    if phone:
        create_payload["properties"]["Teléfono"] = {"phone_number": str(phone)}
        
    url_create = "https://api.notion.com/v1/pages"
    res_create = requests.post(url_create, headers=HEADERS_NOTION, json=create_payload)
    if res_create.status_code == 200:
        return res_create.json()["id"]
    return None

def get_existing_projects():
    """Obtiene los nombres de todos los proyectos existentes para evitar duplicados"""
    print("📋 Obteniendo proyectos existentes para evitar duplicados...")
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
    
    projects = set()
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor: payload["start_cursor"] = cursor
        
        try:
            res = requests.post(url, headers=HEADERS_NOTION, json=payload)
            if res.status_code == 200:
                data = res.json()
                for p in data.get("results", []):
                    try:
                        title = p["properties"]["Nombre"]["title"][0]["text"]["content"]
                        projects.add(title)
                    except: pass
                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")
            else:
                print(f"   ⚠️ Error leyendo Notion: {res.text}")
                has_more = False
        except Exception as e:
            print(f"   ⚠️ Excepción leyendo Notion: {e}")
            has_more = False
            
    print(f"   ✓ Encontrados {len(projects)} proyectos previos.")
    return projects

def import_trello_to_notion():
    print(f"\n🚀 Iniciando importación de Trello a Notion (Últimos 3 meses)...")
    
    # 1. Obtener proyectos ya importados
    existing_projects = get_existing_projects()
    
    # Fecha límite (hace 90 días)
    limit_date = datetime.now() - timedelta(days=90)
    print(f"📅 Filtrando tarjetas activas después de: {limit_date.strftime('%Y-%m-%d')}")

    cards = get_trello_cards()
    
    # Filtrar por fecha de última actividad
    filtered_cards = []
    for card in cards:
        try:
            val = card.get('dateLastActivity')
            if val:
                last_activity = datetime.strptime(val.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                if last_activity > limit_date:
                    filtered_cards.append(card)
        except: pass
            
    print(f"📊 Total tarjetas encontradas: {len(cards)}")
    print(f"✨ Tarjetas a importar (últimos 3 meses): {len(filtered_cards)}")
    
    cards = filtered_cards 
    lists_map = get_trello_lists()
    cc_map = get_cc_mapping()
    
    cf_defs_url = f"https://api.trello.com/1/boards/{BOARD_ID}/customFields"
    cf_defs = requests.get(cf_defs_url, params = config.get_trello_params()).json()
    cf_names = {cf['id']: cf['name'] for cf in cf_defs}
    
    count = 0
    skipped = 0
    limit = 2000 
    
    for card in cards:
        if count >= limit: break
        
        card_name = card['name']
        
        # CHEQUEO DE INDEMPOTENCIA
        if card_name in existing_projects:
            print(f"⏩ Saltando duplicado: {card_name}")
            skipped += 1
            continue
            
        list_name = lists_map.get(card['idList'], "")
        notion_status = ESTADOS_MAP.get(list_name, "Cotización")
        if "Freezer" in list_name: notion_status = "Cancelado" 
        
        print(f"\nProcesando: {card_name}")
        print(f"   Estado Trello: {list_name} -> Notion: {notion_status}")
        
        # Procesar Custom Fields
        email = None
        phone = None
        monto = 0
        
        for cf in card.get('customFieldItems', []):
            field_name = cf_names.get(cf['idCustomField'], "")
            val = cf.get('value', {})
            
            if "Mail" in field_name and 'text' in val:
                email = val['text']
            if "Celular" in field_name and 'number' in val:
                phone = val['number']
            if "monto" in field_name.lower() and 'number' in val:
                try: monto = float(val['number'])
                except: pass

        # Gestionar Cliente
        client_id = find_or_create_client(card_name.split("-")[0].strip(), email, phone) 
        
        # Gestionar Centro de Costo
        cc_id = None
        for label in card['labels']:
            for key, val in cc_map.items():
                if key in label['name']:
                    cc_id = val
                    break
        
        # Crear Proyecto en Notion
        props = {
            "Nombre": {"title": [{"text": {"content": card_name}}]},
            "Estado": {"select": {"name": notion_status}},
        }
        
        if client_id:
            props["Cliente"] = {"relation": [{"id": client_id}]}
        if cc_id:
            props["Centro de Costo"] = {"relation": [{"id": cc_id}]}
        if monto > 0:
            props["Monto Contrato"] = {"number": monto}
            
        url_page = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": PROYECTOS_DB_ID},
            "properties": props
        }
        
        # RETRY LOGIC
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = requests.post(url_page, headers=HEADERS_NOTION, json=payload)
                if res.status_code == 200:
                    print("   ✅ Proyecto creado.")
                    count += 1
                    break
                else:
                    print(f"   ❌ Error Notion ({res.status_code}): {res.text}")
                    time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Error de conexión (Intento {attempt+1}/{max_retries}): {e}")
                time.sleep(5)
            
        time.sleep(0.2) 

    print(f"\n✨ Importación finalizada.")
    print(f"   ✅ Creados: {count}")
    print(f"   ⏩ Saltados (ya existían): {skipped}")


if __name__ == "__main__":
    import_trello_to_notion()
