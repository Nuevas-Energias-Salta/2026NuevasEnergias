"""
Script CORREGIDO para crear tablas de Resumen Financiero
Calcula automáticamente basándose en el Estado de cada cuenta
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


# Configuración
config.NOTION_TOKEN
PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"  # Gestión Financiera
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def get_all_pages(db_id):
    """Obtiene todas las páginas de una base de datos"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    results = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            cursor = data.get("next_cursor")
        else:
            break
    
    return results

def calculate_cxc_totals():
    """Calcula los totales de CxC sumando las columnas directamente"""
    print("\n📤 Calculando totales de Cuentas por Cobrar...")
    
    pages = get_all_pages(CXC_DB_ID)
    
    total_monto = 0
    total_cobrado = 0
    total_pendiente = 0
    
    for page in pages:
        props = page["properties"]
        
        # Sumar Monto (tipo: number)
        monto = props.get("Monto", {}).get("number", 0) or 0
        total_monto += monto
        
        # Sumar Monto Cobrado (tipo: rollup)
        cobrado_prop = props.get("Monto Cobrado", {})
        if cobrado_prop.get("type") == "rollup":
            rollup_data = cobrado_prop.get("rollup", {})
            cobrado = rollup_data.get("number", 0) or 0
        else:
            cobrado = 0
        total_cobrado += cobrado
        
        # Sumar Saldo Pendiente (tipo: formula)
        saldo_prop = props.get("Saldo Pendiente", {})
        if saldo_prop.get("type") == "formula":
            formula_data = saldo_prop.get("formula", {})
            pendiente = formula_data.get("number", 0) or 0
        else:
            pendiente = 0
        total_pendiente += pendiente
    
    print(f"   ✓ {len(pages)} cuentas procesadas")
    print(f"   💰 Monto Total: ${total_monto:,.0f}")
    print(f"   ✅ Monto Cobrado: ${total_cobrado:,.0f}")
    print(f"   ⏳ Saldo Pendiente: ${total_pendiente:,.0f}")
    
    return total_monto, total_cobrado, total_pendiente

def calculate_cxp_totals():
    """Calcula los totales de CxP sumando las columnas directamente"""
    print("\n📥 Calculando totales de Cuentas por Pagar...")
    
    pages = get_all_pages(CXP_DB_ID)
    
    total_monto = 0
    total_pagado = 0
    total_pendiente = 0
    
    for page in pages:
        props = page["properties"]
        
        # Sumar Monto
        monto = props.get("Monto", {}).get("number", 0) or 0
        total_monto += monto
        
        # Sumar Monto Pagado (columna existente)
        pagado = props.get("Monto Pagado", {}).get("number", 0) or 0
        total_pagado += pagado
        
        # Sumar Saldo Pendiente (columna existente)
        pendiente = props.get("Saldo Pendiente", {}).get("number", 0) or 0
        total_pendiente += pendiente
    
    print(f"   ✓ {len(pages)} cuentas procesadas")
    print(f"   💳 Monto Total: ${total_monto:,.0f}")
    print(f"   ✅ Monto Pagado: ${total_pagado:,.0f}")
    print(f"   ⏳ Saldo Pendiente: ${total_pendiente:,.0f}")
    
    return total_monto, total_pagado, total_pendiente

def update_or_create_resumen_cxc(total_monto, total_cobrado, total_pendiente):
    """Actualiza o crea la base de datos Resumen CxC"""
    print("\n📊 Actualizando tabla 'Resumen CxC'...")
    
    # Buscar si ya existe
    url_search = f"{BASE_URL}/search"
    search_payload = {
        "query": "📤 Resumen CxC",
        "filter": {"property": "object", "value": "database"}
    }
    
    search_res = requests.post(url_search, headers=HEADERS, json=search_payload)
    
    db_id = None
    if search_res.status_code == 200:
        results = search_res.json().get("results", [])
        for result in results:
            if "📤 Resumen CxC" in result.get("title", [{}])[0].get("text", {}).get("content", ""):
                db_id = result["id"]
                print(f"   ✓ Base de datos existente encontrada")
                break
    
    if not db_id:
        # Crear nueva base de datos
        url = f"{BASE_URL}/databases"
        
        properties = {
            "Concepto": {"title": {}},
            "Monto Total": {"number": {"format": "argentine_peso"}},
            "Monto Cobrado": {"number": {"format": "argentine_peso"}},
            "Saldo Pendiente": {"number": {"format": "argentine_peso"}}
        }
        
        payload = {
            "parent": {"type": "page_id", "page_id": PAGE_ID},
            "title": [{"type": "text", "text": {"content": "📤 Resumen CxC"}}],
            "icon": {"type": "emoji", "emoji": "📤"},
            "properties": properties
        }
        
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            db_id = response.json()["id"]
            print("   ✓ Base de datos creada")
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    
    # Buscar si ya existe una entrada
    url_query = f"{BASE_URL}/databases/{db_id}/query"
    query_res = requests.post(url_query, headers=HEADERS, json={})
    
    page_id = None
    if query_res.status_code == 200:
        pages = query_res.json().get("results", [])
        if pages:
            page_id = pages[0]["id"]
    
    if page_id:
        # Actualizar entrada existente
        print("   ✓ Actualizando entrada existente...")
        url_update = f"{BASE_URL}/pages/{page_id}"
        update_payload = {
            "properties": {
                "Monto Total": {"number": round(total_monto, 2)},
                "Monto Cobrado": {"number": round(total_cobrado, 2)},
                "Saldo Pendiente": {"number": round(total_pendiente, 2)}
            }
        }
        res = requests.patch(url_update, headers=HEADERS, json=update_payload)
    else:
        # Crear nueva entrada
        print("   ✓ Creando entrada de totales...")
        url_page = f"{BASE_URL}/pages"
        page_payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Concepto": {"title": [{"text": {"content": "Totales"}}]},
                "Monto Total": {"number": round(total_monto, 2)},
                "Monto Cobrado": {"number": round(total_cobrado, 2)},
                "Saldo Pendiente": {"number": round(total_pendiente, 2)}
            }
        }
        res = requests.post(url_page, headers=HEADERS, json=page_payload)
    
    if res.status_code in [200, 201]:
        print("   ✓ Tabla actualizada correctamente")
        return True
    else:
        print(f"   ❌ Error: {res.status_code}")
        return False

def update_or_create_resumen_cxp(total_monto, total_pagado, total_pendiente):
    """Actualiza o crea la base de datos Resumen CxP"""
    print("\n📊 Actualizando tabla 'Resumen CxP'...")
    
    # Buscar si ya existe
    url_search = f"{BASE_URL}/search"
    search_payload = {
        "query": "📥 Resumen CxP",
        "filter": {"property": "object", "value": "database"}
    }
    
    search_res = requests.post(url_search, headers=HEADERS, json=search_payload)
    
    db_id = None
    if search_res.status_code == 200:
        results = search_res.json().get("results", [])
        for result in results:
            if "📥 Resumen CxP" in result.get("title", [{}])[0].get("text", {}).get("content", ""):
                db_id = result["id"]
                print(f"   ✓ Base de datos existente encontrada")
                break
    
    if not db_id:
        # Crear nueva base de datos
        url = f"{BASE_URL}/databases"
        
        properties = {
            "Concepto": {"title": {}},
            "Monto Total": {"number": {"format": "argentine_peso"}},
            "Monto Pagado": {"number": {"format": "argentine_peso"}},
            "Saldo Pendiente": {"number": {"format": "argentine_peso"}}
        }
        
        payload = {
            "parent": {"type": "page_id", "page_id": PAGE_ID},
            "title": [{"type": "text", "text": {"content": "📥 Resumen CxP"}}],
            "icon": {"type": "emoji", "emoji": "📥"},
            "properties": properties
        }
        
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            db_id = response.json()["id"]
            print("   ✓ Base de datos creada")
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    
    # Buscar si ya existe una entrada
    url_query = f"{BASE_URL}/databases/{db_id}/query"
    query_res = requests.post(url_query, headers=HEADERS, json={})
    
    page_id = None
    if query_res.status_code == 200:
        pages = query_res.json().get("results", [])
        if pages:
            page_id = pages[0]["id"]
    
    if page_id:
        # Actualizar entrada existente
        print("   ✓ Actualizando entrada existente...")
        url_update = f"{BASE_URL}/pages/{page_id}"
        update_payload = {
            "properties": {
                "Monto Total": {"number": round(total_monto, 2)},
                "Monto Pagado": {"number": round(total_pagado, 2)},
                "Saldo Pendiente": {"number": round(total_pendiente, 2)}
            }
        }
        res = requests.patch(url_update, headers=HEADERS, json=update_payload)
    else:
        # Crear nueva entrada
        print("   ✓ Creando entrada de totales...")
        url_page = f"{BASE_URL}/pages"
        page_payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Concepto": {"title": [{"text": {"content": "Totales"}}]},
                "Monto Total": {"number": round(total_monto, 2)},
                "Monto Pagado": {"number": round(total_pagado, 2)},
                "Saldo Pendiente": {"number": round(total_pendiente, 2)}
            }
        }
        res = requests.post(url_page, headers=HEADERS, json=page_payload)
    
    if res.status_code in [200, 201]:
        print("   ✓ Tabla actualizada correctamente")
        return True
    else:
        print(f"   ❌ Error: {res.status_code}")
        return False

def main():
    print("=" * 60)
    print("📊 ACTUALIZANDO TABLAS DE RESUMEN FINANCIERO")
    print("=" * 60)
    print("\n💡 Sumando columnas directamente (Monto, Monto Cobrado/Pagado, Saldo Pendiente)...")
    
    # Calcular totales
    cxc_total, cxc_cobrado, cxc_pendiente = calculate_cxc_totals()
    cxp_total, cxp_pagado, cxp_pendiente = calculate_cxp_totals()
    
    # Actualizar/crear tablas
    success_cxc = update_or_create_resumen_cxc(cxc_total, cxc_cobrado, cxc_pendiente)
    success_cxp = update_or_create_resumen_cxp(cxp_total, cxp_pagado, cxp_pendiente)
    
    print("\n" + "=" * 60)
    if success_cxc and success_cxp:
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n📊 Resumen:")
        print(f"\n📤 CxC:")
        print(f"   Monto Total: ${cxc_total:,.0f}")
        print(f"   Monto Cobrado: ${cxc_cobrado:,.0f}")
        print(f"   Saldo Pendiente: ${cxc_pendiente:,.0f}")
        print(f"\n📥 CxP:")
        print(f"   Monto Total: ${cxp_total:,.0f}")
        print(f"   Monto Pagado: ${cxp_pagado:,.0f}")
        print(f"   Saldo Pendiente: ${cxp_pendiente:,.0f}")
        print("\n💡 Abrí Notion → 'Gestión Financiera' para ver las tablas actualizadas!")
    else:
        print("⚠️ PROCESO COMPLETADO CON ERRORES")
        print("=" * 60)

if __name__ == "__main__":
    main()
