"""
Script para crear el Dashboard del ERP en Notion
Crea vistas filtradas y el panel de control principal
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import json
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import config


# Configuración
TOKEN = config.NOTION_TOKEN
PAGE_ID = config.NOTION_PAGE_ID
HEADERS = config.get_notion_headers()
BASE_URL = config.NOTION_BASE_URL

# IDs de las bases de datos
CENTROS_DB_ID = config.CENTROS_DB_ID
CLIENTES_DB_ID = config.CLIENTES_DB_ID
PROVEEDORES_DB_ID = config.PROVEEDORES_DB_ID
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = config.CXC_DB_ID
CXP_DB_ID = config.CXP_DB_ID

def create_page(parent_id, title, icon, children=None):
    """Crea una página en Notion"""
    url = f"{BASE_URL}/pages"
    
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        "icon": {"type": "emoji", "emoji": icon}
    }
    
    if children:
        payload["children"] = children
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Página '{title}' creada exitosamente!")
        return response.json()
    else:
        print(f"❌ Error creando página '{title}': {response.status_code}")
        print(response.text)
        return None

def create_heading(text, level=1):
    """Crea un bloque de encabezado"""
    heading_type = f"heading_{level}"
    return {
        "object": "block",
        "type": heading_type,
        heading_type: {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def create_callout(text, icon="💡", color="gray_background"):
    """Crea un bloque callout"""
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": icon},
            "color": color
        }
    }

def create_divider():
    """Crea un divisor"""
    return {
        "object": "block",
        "type": "divider",
        "divider": {}
    }

def create_linked_database(database_id):
    """Crea un linked database embed"""
    return {
        "object": "block",
        "type": "child_database",
        "child_database": {
            "title": "Linked"
        }
    }

def create_paragraph(text):
    """Crea un párrafo"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def create_toggle(title, children=None):
    """Crea un toggle"""
    toggle = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": title}}]
        }
    }
    if children:
        toggle["toggle"]["children"] = children
    return toggle

def create_table_of_contents():
    """Crea tabla de contenidos"""
    return {
        "object": "block",
        "type": "table_of_contents",
        "table_of_contents": {
            "color": "gray"
        }
    }

def create_column_list(columns):
    """Crea columnas"""
    return {
        "object": "block",
        "type": "column_list",
        "column_list": {
            "children": columns
        }
    }

def create_column(children):
    """Crea una columna"""
    return {
        "object": "block",
        "type": "column",
        "column": {
            "children": children
        }
    }

def append_blocks(page_id, blocks):
    """Añade bloques a una página"""
    url = f"{BASE_URL}/blocks/{page_id}/children"
    
    payload = {"children": blocks}
    
    response = requests.patch(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error añadiendo bloques: {response.status_code}")
        print(response.text)
        return None

# ============================================
# CREAR DASHBOARD PRINCIPAL
# ============================================
def create_dashboard():
    print("\n📊 Creando Dashboard Principal...")
    
    # Contenido inicial del Dashboard
    children = [
        create_heading("📊 Dashboard Financiero", 1),
        create_paragraph("Panel de control para gestión de cuentas por cobrar y pagar."),
        create_divider(),
        
        # Sección de Resumen
        create_heading("💰 Resumen General", 2),
        create_callout("Total por Cobrar: Consultar en Cuentas por Cobrar → Vista 'Pendientes'", "📤", "green_background"),
        create_callout("Total por Pagar: Consultar en Cuentas por Pagar → Vista 'Pendientes'", "📥", "red_background"),
        create_callout("Balance = Por Cobrar - Por Pagar", "📊", "blue_background"),
        create_divider(),
        
        # Alertas
        create_heading("🚨 Alertas", 2),
        create_callout("Revisar Cuentas VENCIDAS en las vistas correspondientes", "⚠️", "yellow_background"),
        create_divider(),
        
        # Links rápidos
        create_heading("🔗 Accesos Rápidos", 2),
        create_paragraph("👇 Hacé clic en cada base de datos para acceder:"),
    ]
    
    dashboard = create_page(PAGE_ID, "📊 Dashboard", "📊", children)
    
    if dashboard:
        dashboard_id = dashboard["id"]
        print(f"   Dashboard ID: {dashboard_id}")
        return dashboard_id
    return None

# ============================================
# CREAR PÁGINAS DE VISTAS
# ============================================
def create_vista_cxc_pendientes():
    print("\n📤 Creando página: Cuentas por Cobrar - Pendientes...")
    
    children = [
        create_heading("📤 Cuentas por Cobrar - Pendientes", 1),
        create_callout("Filtrá por Estado = 'Pendiente' para ver solo las pendientes", "💡", "blue_background"),
        create_paragraph("⬇️ Ir a la base de datos 'Cuentas por Cobrar' y crear vista filtrada por Estado = Pendiente"),
        create_divider(),
        create_heading("Instrucciones:", 2),
        create_paragraph("1. Abrí la base de datos 'Cuentas por Cobrar'"),
        create_paragraph("2. Hacé clic en '+ Add a view' (arriba a la izquierda)"),
        create_paragraph("3. Elegí 'Table' y nombrala 'Pendientes'"),
        create_paragraph("4. Hacé clic en 'Filter' → Add filter"),
        create_paragraph("5. Estado = Pendiente"),
        create_paragraph("6. Ordenar por 'Fecha Vencimiento' ascendente"),
    ]
    
    page = create_page(PAGE_ID, "📤 CxC Pendientes", "📤", children)
    return page["id"] if page else None

def create_vista_cxc_vencidas():
    print("\n🔴 Creando página: Cuentas por Cobrar - Vencidas...")
    
    children = [
        create_heading("🔴 Cuentas por Cobrar - Vencidas", 1),
        create_callout("¡ATENCIÓN! Estas cuentas están vencidas y requieren seguimiento", "⚠️", "red_background"),
        create_paragraph("⬇️ Ir a la base de datos 'Cuentas por Cobrar' y crear vista filtrada por Estado = Vencido"),
        create_divider(),
        create_heading("Instrucciones:", 2),
        create_paragraph("1. Abrí la base de datos 'Cuentas por Cobrar'"),
        create_paragraph("2. Hacé clic en '+ Add a view'"),
        create_paragraph("3. Elegí 'Table' y nombrala 'Vencidas'"),
        create_paragraph("4. Hacé clic en 'Filter' → Estado = Vencido"),
    ]
    
    page = create_page(PAGE_ID, "🔴 CxC Vencidas", "🔴", children)
    return page["id"] if page else None

def create_vista_cxp_pendientes():
    print("\n📥 Creando página: Cuentas por Pagar - Pendientes...")
    
    children = [
        create_heading("📥 Cuentas por Pagar - Pendientes", 1),
        create_callout("Pagos pendientes ordenados por fecha de vencimiento", "💡", "orange_background"),
        create_paragraph("⬇️ Ir a la base de datos 'Cuentas por Pagar' y crear vista filtrada por Estado = Pendiente"),
        create_divider(),
        create_heading("Instrucciones:", 2),
        create_paragraph("1. Abrí la base de datos 'Cuentas por Pagar'"),
        create_paragraph("2. Hacé clic en '+ Add a view'"),
        create_paragraph("3. Elegí 'Table' y nombrala 'Pendientes'"),
        create_paragraph("4. Hacé clic en 'Filter' → Estado = Pendiente"),
        create_paragraph("5. Ordenar por 'Fecha Vencimiento' ascendente"),
    ]
    
    page = create_page(PAGE_ID, "📥 CxP Pendientes", "📥", children)
    return page["id"] if page else None

def create_vista_cxp_vencidas():
    print("\n🔴 Creando página: Cuentas por Pagar - Vencidas...")
    
    children = [
        create_heading("🔴 Cuentas por Pagar - Vencidas", 1),
        create_callout("¡URGENTE! Pagos vencidos que requieren atención inmediata", "🚨", "red_background"),
        create_paragraph("⬇️ Ir a la base de datos 'Cuentas por Pagar' y crear vista filtrada por Estado = Vencido"),
    ]
    
    page = create_page(PAGE_ID, "🔴 CxP Vencidas", "🔴", children)
    return page["id"] if page else None

def create_vista_proyectos_activos():
    print("\n🏗️ Creando página: Proyectos Activos...")
    
    children = [
        create_heading("🏗️ Proyectos en Ejecución", 1),
        create_callout("Proyectos actualmente en curso", "💡", "yellow_background"),
        create_paragraph("⬇️ Ir a la base de datos 'Proyectos/Obras' y crear vista filtrada por Estado = En Ejecución"),
        create_divider(),
        create_heading("Instrucciones:", 2),
        create_paragraph("1. Abrí la base de datos 'Proyectos/Obras'"),
        create_paragraph("2. Hacé clic en '+ Add a view'"),
        create_paragraph("3. Elegí 'Board' (tablero Kanban) y nombrala 'Por Estado'"),
        create_paragraph("4. Agrupar por 'Estado'"),
    ]
    
    page = create_page(PAGE_ID, "🏗️ Proyectos Activos", "🏗️", children)
    return page["id"] if page else None

# ============================================
# CREAR VISTAS DIRECTAMENTE EN LAS BDS
# ============================================
def add_views_instructions_to_db(db_id, db_name, views_info):
    """Las vistas en Notion no se pueden crear via API, 
    pero podemos documentar cómo crearlas"""
    print(f"\n📝 Instrucciones para crear vistas en {db_name}:")
    for view in views_info:
        print(f"   - {view['name']}: Filtrar por {view['filter']}")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 50)
    print("📊 CREANDO DASHBOARD Y VISTAS")
    print("=" * 50)
    
    # Crear Dashboard principal
    dashboard_id = create_dashboard()
    time.sleep(1)
    
    # Crear páginas de vistas
    create_vista_cxc_pendientes()
    time.sleep(0.5)
    
    create_vista_cxc_vencidas()
    time.sleep(0.5)
    
    create_vista_cxp_pendientes()
    time.sleep(0.5)
    
    create_vista_cxp_vencidas()
    time.sleep(0.5)
    
    create_vista_proyectos_activos()
    
    # Instrucciones para crear vistas en las BDs
    print("\n" + "=" * 50)
    print("📝 VISTAS A CREAR MANUALMENTE EN CADA BD")
    print("=" * 50)
    
    print("\n📤 En 'Cuentas por Cobrar' crear estas vistas:")
    print("   1. 'Pendientes' → Filtro: Estado = Pendiente")
    print("   2. 'Vencidos' → Filtro: Estado = Vencido")
    print("   3. 'Cobrados este mes' → Filtro: Fecha Cobro = Este mes")
    print("   4. 'Por Centro de Costo' → Agrupar por Centro de Costo")
    print("   5. 'Calendario' → Vista Calendario por Fecha Vencimiento")
    
    print("\n📥 En 'Cuentas por Pagar' crear estas vistas:")
    print("   1. 'Pendientes' → Filtro: Estado = Pendiente")
    print("   2. 'Vencidos' → Filtro: Estado = Vencido")
    print("   3. 'Pagados este mes' → Filtro: Fecha Pago = Este mes")
    print("   4. 'Por Centro de Costo' → Agrupar por Centro de Costo")
    print("   5. 'Por Proyecto' → Agrupar por Proyecto")
    
    print("\n🏗️ En 'Proyectos/Obras' crear estas vistas:")
    print("   1. 'Tablero Kanban' → Vista Board agrupada por Estado")
    print("   2. 'En Ejecución' → Filtro: Estado = En Ejecución")
    print("   3. 'Finalizados' → Filtro: Estado = Finalizado")
    
    print("\n" + "=" * 50)
    print("✅ PROCESO COMPLETADO")
    print("=" * 50)
    print(f"\n📊 Dashboard ID: {dashboard_id}")
    print("\n¡Revisá tu Notion! Se crearon las páginas de guía.")
    print("Ahora seguí las instrucciones para crear las vistas en cada BD.")

if __name__ == "__main__":
    main()
