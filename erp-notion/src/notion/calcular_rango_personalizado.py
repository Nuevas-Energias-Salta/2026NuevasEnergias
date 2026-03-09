"""
Script interactivo para calcular totales de un rango de fechas personalizado
El usuario ingresa fecha inicio y fecha fin, y se actualiza la fila "Rango Personalizado"
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

from datetime import datetime

config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

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
    
    for page in pages:
        props = page["properties"]
        
        # Filtrar por fecha
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
    
    total_pendiente = total_monto - total_cobrado
    return total_monto, total_cobrado, total_pendiente

def find_resumen_cxc():
    """Busca la base de datos Resumen CxC"""
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
    return None

def update_custom_range(db_id, period_name, monto_total, monto_cobrado, saldo_pendiente):
    """Actualiza o crea la fila de rango personalizado"""
    # Buscar si ya existe
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
    print("📅 CÁLCULO DE RANGO PERSONALIZADO - RESUMEN CXC")
    print("=" * 60)
    
    # Solicitar fechas
    print("\n📋 Ingresá el rango de fechas:")
    print("   Formato: YYYY-MM-DD (ejemplo: 2025-12-01)")
    
    fecha_inicio_str = input("\n📅 Fecha inicio: ").strip()
    fecha_fin_str = input("📅 Fecha fin: ").strip()
    
    # Validar fechas
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    except ValueError:
        print("\n❌ Error: Formato de fecha inválido")
        print("   Usá el formato: YYYY-MM-DD (ejemplo: 2025-12-01)")
        return
    
    if fecha_inicio > fecha_fin:
        print("\n❌ Error: La fecha inicio debe ser anterior a la fecha fin")
        return
    
    print(f"\n✓ Rango: {fecha_inicio_str} a {fecha_fin_str}")
    
    # Obtener cuentas
    print("\n📤 Obteniendo cuentas por cobrar...")
    all_cxc = get_all_cxc()
    print(f"   ✓ {len(all_cxc)} cuentas encontradas")
    
    # Calcular totales
    print("\n💰 Calculando totales del rango...")
    total, cobrado, pendiente = calculate_totals_for_period(
        all_cxc, 
        start_date=fecha_inicio.replace(hour=0, minute=0, second=0),
        end_date=fecha_fin.replace(hour=23, minute=59, second=59)
    )
    
    print(f"\n📊 Resultados:")
    print(f"   Monto Total: ${total:,.0f}")
    print(f"   Monto Cobrado: ${cobrado:,.0f}")
    print(f"   Saldo Pendiente: ${pendiente:,.0f}")
    
    # Buscar Resumen CxC
    print("\n📊 Buscando Resumen CxC...")
    resumen_db_id = find_resumen_cxc()
    if not resumen_db_id:
        print("   ❌ No se encontró Resumen CxC")
        return
    
    # Actualizar fila
    period_name = f"Rango: {fecha_inicio_str} a {fecha_fin_str}"
    print(f"\n💾 Guardando en Resumen CxC...")
    
    if update_custom_range(resumen_db_id, period_name, total, cobrado, pendiente):
        print("   ✓ Fila actualizada correctamente")
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO")
        print("=" * 60)
        print(f"\n💡 Abrí 'Resumen CxC' en Notion para ver la fila:")
        print(f"   '{period_name}'")
    else:
        print("   ❌ Error al actualizar")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
