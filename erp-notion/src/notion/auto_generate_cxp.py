"""
Script para auto-generar Cuentas por Pagar desde los Proyectos.
Genera CxP estimadas basadas en percentajes del monto del proyecto.
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from datetime import datetime, timedelta
import random
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


# Configuración
config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"
PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

# Configuración de generación de gastos por proyecto
# Los porcentajes suman aproximadamente 100% del costo
GASTOS_CONFIG = [
    {"categoria": "Materiales", "porcentaje": 0.55, "dias_factura": -5, "dias_venc": 15},
    {"categoria": "Materiales", "porcentaje": 0.15, "dias_factura": 10, "dias_venc": 30},  # Segunda compra
    {"categoria": "Mano de Obra", "porcentaje": 0.20, "dias_factura": 5, "dias_venc": 20},
    {"categoria": "Transporte", "porcentaje": 0.05, "dias_factura": -3, "dias_venc": 10},
    {"categoria": "Otros", "porcentaje": 0.05, "dias_factura": 15, "dias_venc": 25},
]

def get_all_projects():
    """Obtiene todos los proyectos con paginación"""
    print("📂 Leyendo proyectos de Notion...")
    url = f"{BASE_URL}/databases/{PROYECTOS_DB_ID}/query"
    
    projects = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor: payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            projects.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            cursor = data.get("next_cursor")
        else:
            print(f"Error: {res.text}")
            break
            
    print(f"   ✓ {len(projects)} proyectos encontrados.")
    return projects

def get_proveedores_by_category(categoria):
    """Obtiene proveedores de una categoría específica"""
    url = f"{BASE_URL}/databases/{PROVEEDORES_DB_ID}/query"
    
    payload = {
        "filter": {
            "property": "Categoría",
            "multi_select": {"contains": categoria}
        }
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        results = res.json().get("results", [])
        return [p["id"] for p in results] if results else []
    return []

def check_existing_cxp(proyecto_id):
    """Verifica si ya existen cuentas por pagar para un proyecto"""
    url = f"{BASE_URL}/databases/{CXP_DB_ID}/query"
    
    payload = {
        "filter": {
            "property": "Proyecto",
            "relation": {"contains": proyecto_id}
        }
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        results = res.json().get("results", [])
        return len(results) > 0, len(results)
    return False, 0

def create_cxp_entry(proyecto, categoria, concepto, monto, fecha_factura, dias_vencimiento, proveedor_id=None):
    """Crea una entrada de cuenta por pagar"""
    try:
        props = proyecto["properties"]
        
        # Centro de Costo
        cc_rel = props.get("Centro de Costo", {}).get("relation", [])
        cc_id = cc_rel[0]["id"] if cc_rel else None
        
        # Estado del proyecto
        estado = props.get("Estado", {}).get("select", {}).get("name", "")
        
        # Decidir estado de la cuenta
        if estado == "Finalizado":
            cuenta_estado = "Pagado"
        elif estado == "Cancelado":
            return None, "Proyecto cancelado"
        else:
            cuenta_estado = "Pendiente"
        
        fecha_vencimiento = fecha_factura + timedelta(days=dias_vencimiento)
        
        # Payload
        cxp_props = {
            "Concepto": {"title": [{"text": {"content": concepto}}]},
            "Proyecto": {"relation": [{"id": proyecto["id"]}]},
            "Categoría": {"select": {"name": categoria}},
            "Monto": {"number": round(monto, 2)},
            "Estado": {"select": {"name": cuenta_estado}},
            "Fecha Factura": {"date": {"start": fecha_factura.strftime("%Y-%m-%d")}},
            "Fecha Vencimiento": {"date": {"start": fecha_vencimiento.strftime("%Y-%m-%d")}}
        }
        
        if cc_id:
            cxp_props["Centro de Costo"] = {"relation": [{"id": cc_id}]}
        
        if proveedor_id:
            cxp_props["Proveedor"] = {"relation": [{"id": proveedor_id}]}
        
        url = f"{BASE_URL}/pages"
        payload = {
            "parent": {"database_id": CXP_DB_ID},
            "properties": cxp_props
        }
        
        res = requests.post(url, headers=HEADERS, json=payload)
        
        if res.status_code == 200:
            return True, f"${monto:,.0f}"
        else:
            return None, f"Error API: {res.status_code}"
            
    except Exception as e:
        return None, f"Excepción: {str(e)[:50]}"

def generate_cxp_for_project(proyecto):
    """Genera cuentas por pagar para un proyecto"""
    try:
        props = proyecto["properties"]
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin nombre")
        monto = props.get("Monto Contrato", {}).get("number")
        
        if not monto or monto <= 0:
            return 0, "Sin monto"
        
        # Verificar duplicados
        existe, cuenta_existente = check_existing_cxp(proyecto["id"])
        if existe:
            return 0, f"Ya tiene {cuenta_existente} cuenta(s)"
        
        today = datetime.now()
        created = 0
        
        # Generar cuentas según configuración
        for idx, gasto in enumerate(GASTOS_CONFIG):
            monto_gasto = monto * gasto["porcentaje"]
            fecha_factura = today + timedelta(days=gasto["dias_factura"])
            
            # Buscar proveedor de la categoría
            proveedores = get_proveedores_by_category(gasto["categoria"])
            proveedor_id = random.choice(proveedores) if proveedores else None
            
            # Generar concepto descriptivo
            if gasto["categoria"] == "Materiales":
                suffix = "Anticipo" if idx == 0 else "Complemento"
                concepto_desc = f"{gasto['categoria']} {suffix} - {nombre}"
            else:
                concepto_desc = f"{gasto['categoria']} - {nombre}"
            
            result, msg = create_cxp_entry(
                proyecto, 
                gasto["categoria"],
                concepto_desc,
                monto_gasto,
                fecha_factura,
                gasto["dias_venc"],
                proveedor_id
            )
            
            if result:
                created += 1
                proveedor_info = "✓" if proveedor_id else "⚠️"
                print(f"      {proveedor_info} {gasto['categoria']}: ${monto_gasto:,.0f}")
        
        return created, f"{created} cuentas creadas"
        
    except Exception as e:
        return 0, f"Error: {str(e)[:50]}"

def main():
    print("=" * 60)
    print("🏗️ AUTO-GENERACIÓN DE CUENTAS POR PAGAR")
    print("=" * 60)
    print(f"\n⚙️ Configuración:")
    print(f"   • Categorías de gasto: {len(GASTOS_CONFIG)}")
    for g in GASTOS_CONFIG:
        print(f"      - {g['categoria']}: {g['porcentaje']*100}%")
    
    projects = get_all_projects()
    
    if not projects:
        print("❌ No hay proyectos para procesar.")
        return
    
    print(f"\n💳 Generando cuentas por pagar...")
    
    total_created = 0
    skipped = 0
    errors = 0
    
    for project in projects:
        try:
            nombre = project["properties"].get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "?")
        except:
            nombre = "Proyecto sin nombre"
        
        print(f"\n   📋 {nombre}")
        
        created, msg = generate_cxp_for_project(project)
        
        if created > 0:
            total_created += created
        elif "Ya tiene" in msg or "Sin" in msg or "cancelado" in msg.lower():
            print(f"      ⏩ {msg}")
            skipped += 1
        else:
            print(f"      ❌ {msg}")
            errors += 1
    
    print("\n" + "=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"   ✅ Cuentas creadas: {total_created}")
    print(f"   ⏩ Proyectos saltados: {skipped}")
    print(f"   ❌ Errores: {errors}")
    print(f"\n💡 Nota: ✓ = con proveedor asignado, ⚠️ = sin proveedor")

if __name__ == "__main__":
    main()
