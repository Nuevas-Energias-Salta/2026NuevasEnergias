"""
Script MEJORADO para actualizar fechas de Trello a Notion
Con mejor manejo de errores y output detallado
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from datetime import datetime, timedelta
import time

# Configuración Trello
config.TRELLO_API_KEY
config.TRELLO_TOKEN
BOARD_ID = "612f6ea39c967b8bef5c2186"

# Configuración Notion
config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

HEADERS_NOTION = {
    f"Bearer {config.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_trello_cards_with_dates():
    """Obtiene tarjetas de Trello con fechas"""
    print("📋 Obteniendo tarjetas de Trello...")
    sys.stdout.flush()
    
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'fields': 'name,dateLastActivity,due,start'
    }
    
    try:
        response = requests.get(url, params=query, timeout=10)
        cards = response.json()
        print(f"   ✓ {len(cards)} tarjetas encontradas")
        sys.stdout.flush()
        return cards
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        sys.stdout.flush()
        return []

def get_notion_projects():
    """Obtiene proyectos de Notion"""
    print("📊 Obteniendo proyectos de Notion...")
    sys.stdout.flush()
    
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
    
    all_projects = []
    page_count = 0
    
    try:
        payload = {"page_size": 50}  # Reducido para mejor manejo
        res = requests.post(url, headers=HEADERS_NOTION, json=payload, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            all_projects = data.get("results", [])
            page_count = 1
            
            # Solo primera página por ahora para probar
            print(f"   ✓ {len(all_projects)} proyectos encontrados (página {page_count})")
            sys.stdout.flush()
        else:
            print(f"   ❌ Error: {res.status_code}")
            sys.stdout.flush()
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        sys.stdout.flush()
    
    return all_projects

def update_project_dates(project_id, project_name, fecha_inicio, fecha_fin):
    """Actualiza fechas de un proyecto"""
    url = f"https://api.notion.com/v1/pages/{project_id}"
    
    properties = {}
    
    if fecha_inicio:
        properties["Fecha Inicio"] = {"date": {"start": fecha_inicio}}
    
    if fecha_fin:
        properties["Fecha Fin Estimada"] = {"date": {"start": fecha_fin}}
    
    if not properties:
        return False
    
    payload = {"properties": properties}
    
    try:
        res = requests.patch(url, headers=HEADERS_NOTION, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"   ✅ {project_name}")
            if fecha_inicio:
                print(f"      📅 Inicio: {fecha_inicio}")
            if fecha_fin:
                print(f"      📅 Fin: {fecha_fin}")
            sys.stdout.flush()
            return True
        else:
            print(f"   ❌ Error {res.status_code}: {project_name}")
            sys.stdout.flush()
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        sys.stdout.flush()
        return False

def main():
    print("=" * 60)
    print("🔄 ACTUALIZANDO FECHAS DESDE TRELLO")
    print("=" * 60)
    sys.stdout.flush()
    
    # Obtener datos
    trello_cards = get_trello_cards_with_dates()
    if not trello_cards:
        print("\n❌ No se pudieron obtener tarjetas de Trello")
        return
    
    notion_projects = get_notion_projects()
    if not notion_projects:
        print("\n❌ No se pudieron obtener proyectos de Notion")
        return
    
    # Crear mapa de Trello
    print(f"\n🗺️ Creando mapa de tarjetas...")
    sys.stdout.flush()
    
    trello_map = {}
    for card in trello_cards:
        trello_map[card['name']] = card
    
    print(f"   ✓ {len(trello_map)} tarjetas mapeadas")
    sys.stdout.flush()
    
    # Procesar
    print(f"\n🔄 Procesando proyectos...\n")
    sys.stdout.flush()
    
    updated = 0
    not_found = 0
    no_dates = 0
    errors = 0
    
    for idx, project in enumerate(notion_projects):
        print(f"[{idx+1}/{len(notion_projects)}] ", end="")
        sys.stdout.flush()
        
        try:
            # Obtener nombre
            props = project["properties"]
            nombre_prop = props.get("Nombre", {}).get("title", [])
            if not nombre_prop:
                print("⏩ Sin nombre")
                sys.stdout.flush()
                continue
            
            nombre = nombre_prop[0].get("text", {}).get("content", "")
            
            # Buscar en Trello
            trello_card = trello_map.get(nombre)
            
            if not trello_card:
                print(f"⚠️ No en Trello: {nombre[:40]}")
                sys.stdout.flush()
                not_found += 1
                continue
            
            # Extraer fechas
            fecha_inicio = None
            fecha_fin = None
            
            # Usar dateLastActivity como referencia
            if trello_card.get('dateLastActivity'):
                try:
                    dt_str = trello_card['dateLastActivity']
                    # Parsear fecha ISO
                    dt = datetime.strptime(dt_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    fecha_inicio = dt.strftime('%Y-%m-%d')
                    # Estimar fin en 30 días
                    fecha_fin = (dt + timedelta(days=30)).strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"⚠️ Error parseando fecha: {nombre[:40]}")
                    sys.stdout.flush()
                    continue
            
            if fecha_inicio or fecha_fin:
                if update_project_dates(project["id"], nombre[:40], fecha_inicio, fecha_fin):
                    updated += 1
                else:
                    errors += 1
            else:
                print(f"⏩ Sin fechas: {nombre[:40]}")
                sys.stdout.flush()
                no_dates += 1
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            sys.stdout.flush()
            errors += 1
    
    print("\n" + "=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"   ✅ Actualizados: {updated}")
    print(f"   ⚠️ No encontrados: {not_found}")
    print(f"   ⏩ Sin fechas: {no_dates}")
    print(f"   ❌ Errores: {errors}")
    sys.stdout.flush()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario")
        sys.stdout.flush()
    except Exception as e:
        print(f"\n\n❌ Error fatal: {str(e)}")
        sys.stdout.flush()
        import traceback
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

        traceback.print_exc()
