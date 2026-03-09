"""
Script para auto-generar Cuentas por Cobrar desde los Proyectos importados de Trello.
Para cada proyecto con monto y cliente, crea una cuenta por cobrar vinculada.
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

# Configuración
config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

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

def create_cuenta_por_cobrar(proyecto):
    """Crea una Cuenta por Cobrar desde un proyecto"""
    try:
        # Extraer datos del proyecto
        props = proyecto["properties"]
        
        # Nombre del proyecto
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin nombre")
        
        # Monto del contrato
        monto = props.get("Monto Contrato", {}).get("number")
        if not monto or monto <= 0:
            return None, "Sin monto"
            
        # Cliente (relación)
        cliente_rel = props.get("Cliente", {}).get("relation", [])
        if not cliente_rel:
            return None, "Sin cliente"
        cliente_id = cliente_rel[0]["id"]
        
        # Centro de Costo (relación)
        cc_rel = props.get("Centro de Costo", {}).get("relation", [])
        cc_id = cc_rel[0]["id"] if cc_rel else None
        
        # Estado del proyecto
        estado = props.get("Estado", {}).get("select", {}).get("name", "")
        
        # Decidir estado de la cuenta según el proyecto
        if estado == "Finalizado":
            cuenta_estado = "Cobrado"
        elif estado == "Cancelado":
            return None, "Proyecto cancelado"
        else:
            cuenta_estado = "Pendiente"
        
        # Crear concepto descriptivo
        concepto = f"Contrato - {nombre}"
        
        # Fechas (estimadas)
        today = datetime.now()
        fecha_emision = today - timedelta(days=10)
        fecha_vencimiento = today + timedelta(days=30)
        
        # Payload para crear cuenta
        cxc_props = {
            "Concepto": {"title": [{"text": {"content": concepto}}]},
            "Cliente": {"relation": [{"id": cliente_id}]},
            "Proyecto": {"relation": [{"id": proyecto["id"]}]},
            "Monto": {"number": monto},
            "Estado": {"select": {"name": cuenta_estado}},
            "Tipo Cobro": {"select": {"name": "Contrato"}},
            "Fecha Emisión": {"date": {"start": fecha_emision.strftime("%Y-%m-%d")}},
            "Fecha Vencimiento": {"date": {"start": fecha_vencimiento.strftime("%Y-%m-%d")}}
        }
        
        if cc_id:
            cxc_props["Centro de Costo"] = {"relation": [{"id": cc_id}]}
        
        url = f"{BASE_URL}/pages"
        payload = {
            "parent": {"database_id": CXC_DB_ID},
            "properties": cxc_props
        }
        
        res = requests.post(url, headers=HEADERS, json=payload)
        
        if res.status_code == 200:
            return True, f"${monto:,.0f}"
        else:
            return None, f"Error API: {res.status_code}"
            
    except Exception as e:
        return None, f"Excepción: {str(e)[:50]}"

def main():
    print("=" * 60)
    print("🏗️ AUTO-GENERACIÓN DE CUENTAS POR COBRAR")
    print("=" * 60)
    
    projects = get_all_projects()
    
    if not projects:
        print("❌ No hay proyectos para procesar.")
        return
    
    print(f"\n💰 Generando cuentas por cobrar...")
    
    created = 0
    skipped = 0
    errors = 0
    
    for project in projects:
        try:
            nombre = project["properties"].get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "?")
        except:
            nombre = "Proyecto sin nombre"
            
        result, msg = create_cuenta_por_cobrar(project)
        
        if result:
            print(f"   ✅ {nombre}: {msg}")
            created += 1
        elif "Sin" in msg or "cancelado" in msg.lower():
            skipped += 1
        else:
            print(f"   ❌ {nombre}: {msg}")
            errors += 1
    
    print("\n" + "=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"   ✅ Cuentas creadas: {created}")
    print(f"   ⏩ Saltadas: {skipped}")
    print(f"   ❌ Errores: {errors}")
    print("\nAhora podés:\n   1. Ver las cuentas en 'Cuentas por Cobrar'\n   2. Activar la suma al pie de la columna 'Monto'")

if __name__ == "__main__":
    main()
