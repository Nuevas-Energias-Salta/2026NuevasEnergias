"""
Script para crear múltiples filas de resumen en Resumen CxC
Una fila por cada período: Total General, Mes Actual, Últimos 30 días, Última Semana
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

from datetime import datetime, timedelta

config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"  # Gestión Financiera

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def get_all_cxc():
    """Obtiene todas las cuentas por cobrar"""
    url = f"{BASE_URL}/databases/{CXC_DB_ID}/query"
    
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

def calculate_totals_for_period(pages, start_date=None, end_date=None):
    """Calcula totales para un período específico"""
    total_monto = 0
    total_cobrado = 0
    total_pendiente = 0
    
    for page in pages:
        props = page["properties"]
        
        # Filtrar por fecha si se especifica
        if start_date or end_date:
            fecha_prop = props.get("Fecha Emisión", {}).get("date")
            if not fecha_prop:
                continue
            
            fecha_str = fecha_prop.get("start")
            if not fecha_str:
                continue
            
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                
                if start_date and fecha < start_date:
                    continue
                if end_date and fecha > end_date:
                    continue
            except:
                continue
        
        # Sumar Monto
        monto = props.get("Monto Base", {}).get("number", 0) or props.get("Monto", {}).get("number", 0) or 0
        total_monto += monto
        
        # Sumar Monto Cobrado (rollup)
        cobrado_prop = props.get("Monto Cobrado Base", {}) or props.get("Monto Cobrado", {})
        if cobrado_prop.get("type") == "rollup":
            rollup_data = cobrado_prop.get("rollup", {})
            cobrado = rollup_data.get("number", 0) or 0
        else:
            cobrado = cobrado_prop.get("number", 0) or 0
        total_cobrado += cobrado
        
        # Sumar Saldo Pendiente (fórmula)
        saldo_prop = props.get("Saldo Pendiente", {})
        if saldo_prop.get("type") == "formula":
            formula_data = saldo_prop.get("formula", {})
            # La fórmula devuelve string, necesitamos el número
            pendiente = monto - cobrado  # Calculamos nosotros
        else:
            pendiente = saldo_prop.get("number", 0) or 0
        total_pendiente += pendiente
    
    return total_monto, total_cobrado, total_pendiente

def find_or_create_resumen_cxc():
    """Busca o crea la base de datos Resumen CxC"""
    # Buscar base de datos
    url = f"{BASE_URL}/search"
    payload = {
        "query": "Resumen CxC",
        "filter": {"property": "object", "value": "database"}
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        results = res.json().get("results", [])
        for result in results:
            title = result.get("title", [{}])[0].get("text", {}).get("content", "")
            if "Resumen CxC" in title:
                return result["id"]
    
    # Si no existe, crearla
    print("Creating Resumen CxC database...")
    url = f"{BASE_URL}/databases"
    payload = {
        "parent": {"page_id": PAGE_ID},
        "title": [{"text": {"content": "📤 Resumen CxC"}}],
        "properties": {
            "Período": {"title": {}},
            "Monto Total": {"number": {"format": "argentine_peso"}},
            "Monto Cobrado": {"number": {"format": "argentine_peso"}},
            "Saldo Pendiente": {"number": {"format": "argentine_peso"}}
        }
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        return res.json()["id"]
    return None

def update_or_create_period_row(db_id, period_name, monto_total, monto_cobrado, saldo_pendiente):
    """Actualiza o crea una fila para un período específico"""
    # Buscar si ya existe la fila
    url = f"{BASE_URL}/databases/{db_id}/query"
    payload = {
        "filter": {
            "property": "Período",
            "title": {"equals": period_name}
        }
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    existing_page = None
    
    if res.status_code == 200:
        results = res.json().get("results", [])
        if results:
            existing_page = results[0]
    
    # Preparar propiedades
    properties = {
        "Período": {"title": [{"text": {"content": period_name}}]},
        "Monto Total": {"number": monto_total},
        "Monto Cobrado": {"number": monto_cobrado},
        "Saldo Pendiente": {"number": saldo_pendiente}
    }
    
    if existing_page:
        # Actualizar
        url = f"{BASE_URL}/pages/{existing_page['id']}"
        payload = {"properties": properties}
        res = requests.patch(url, headers=HEADERS, json=payload)
    else:
        # Crear
        url = f"{BASE_URL}/pages"
        payload = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        res = requests.post(url, headers=HEADERS, json=payload)
    
    return res.status_code == 200

def main():
    print("=" * 60)
    print("📊 ACTUALIZANDO RESUMEN CXC POR PERÍODOS")
    print("=" * 60)
    
    # Obtener todas las cuentas
    print("\n📤 Obteniendo cuentas por cobrar...")
    all_cxc = get_all_cxc()
    print(f"   ✓ {len(all_cxc)} cuentas encontradas")
    
    # Buscar/crear base de datos Resumen
    print("\n📊 Buscando Resumen CxC...")
    resumen_db_id = find_or_create_resumen_cxc()
    if not resumen_db_id:
        print("   ❌ No se pudo encontrar o crear Resumen CxC")
        return
    print(f"   ✓ Resumen CxC encontrado")
    
    # Calcular períodos
    now = datetime.now()
    
    # 1. Total General
    print("\n📊 Calculando: Total General")
    total, cobrado, pendiente = calculate_totals_for_period(all_cxc)
    update_or_create_period_row(resumen_db_id, "Total General", total, cobrado, pendiente)
    print(f"   Total: ${total:,.0f} | Cobrado: ${cobrado:,.0f} | Pendiente: ${pendiente:,.0f}")
    
    # 2. Mes Actual
    print("\n📊 Calculando: Mes Actual")
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total, cobrado, pendiente = calculate_totals_for_period(all_cxc, start_date=start_month)
    update_or_create_period_row(resumen_db_id, "Mes Actual", total, cobrado, pendiente)
    print(f"   Total: ${total:,.0f} | Cobrado: ${cobrado:,.0f} | Pendiente: ${pendiente:,.0f}")
    
    # 3. Últimos 30 días
    print("\n📊 Calculando: Últimos 30 días")
    last_30 = now - timedelta(days=30)
    total, cobrado, pendiente = calculate_totals_for_period(all_cxc, start_date=last_30)
    update_or_create_period_row(resumen_db_id, "Últimos 30 días", total, cobrado, pendiente)
    print(f"   Total: ${total:,.0f} | Cobrado: ${cobrado:,.0f} | Pendiente: ${pendiente:,.0f}")
    
    # 4. Última Semana
    print("\n📊 Calculando: Última Semana")
    last_week = now - timedelta(days=7)
    total, cobrado, pendiente = calculate_totals_for_period(all_cxc, start_date=last_week)
    update_or_create_period_row(resumen_db_id, "Última Semana", total, cobrado, pendiente)
    print(f"   Total: ${total:,.0f} | Cobrado: ${cobrado:,.0f} | Pendiente: ${pendiente:,.0f}")
    
    print("\n" + "=" * 60)
    print("✅ RESUMEN ACTUALIZADO")
    print("=" * 60)
    print("\n💡 Ahora en 'Resumen CxC' tenés 4 filas:")
    print("   1. Total General")
    print("   2. Mes Actual")
    print("   3. Últimos 30 días")
    print("   4. Última Semana")
    print("\n📌 Podés crear vistas filtradas por 'Período' en Notion")

if __name__ == "__main__":
    main()
