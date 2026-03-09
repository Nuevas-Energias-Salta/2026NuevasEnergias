"""
Script para cargar datos de ejemplo en el ERP de Notion
Carga clientes, proveedores, proyectos y cuentas para poder visualizar gráficos
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

import random

# Configuración
config.NOTION_TOKEN

# IDs de las bases de datos
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"
CLIENTES_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"
PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def add_entry(database_id, properties):
    """Agrega una entrada a una base de datos"""
    url = f"{BASE_URL}/pages"
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"Error: {response.status_code} - {response.text[:100]}")
        return None

def get_centro_costo_id(codigo):
    """Obtiene el ID de un centro de costo por su código"""
    url = f"{BASE_URL}/databases/{CENTROS_DB_ID}/query"
    
    payload = {
        "filter": {
            "property": "Código",
            "number": {"equals": codigo}
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200 and response.json()["results"]:
        return response.json()["results"][0]["id"]
    return None

def format_date(date):
    """Formatea una fecha para Notion"""
    return date.strftime("%Y-%m-%d")

# ============================================
# CARGAR CLIENTES
# ============================================
def load_clientes():
    print("\n👥 Cargando clientes de ejemplo...")
    
    clientes = [
        {"nombre": "Juan Pérez", "tipo": "Particular", "email": "juan.perez@email.com", "telefono": "+54 11 5555-1234"},
        {"nombre": "Empresa Solar SA", "tipo": "Empresa", "email": "contacto@empresasolar.com", "telefono": "+54 11 4444-5678"},
        {"nombre": "María García", "tipo": "Particular", "email": "maria.garcia@email.com", "telefono": "+54 351 555-9876"},
        {"nombre": "Constructora del Norte SRL", "tipo": "Empresa", "email": "info@constructoranorte.com", "telefono": "+54 381 444-3210"},
        {"nombre": "Municipalidad de Córdoba", "tipo": "Organismo Público", "email": "energias@cordoba.gob.ar", "telefono": "+54 351 433-0000"},
    ]
    
    cliente_ids = []
    for c in clientes:
        props = {
            "Nombre": {"title": [{"text": {"content": c["nombre"]}}]},
            "Tipo": {"select": {"name": c["tipo"]}},
            "Email": {"email": c["email"]},
            "Teléfono": {"phone_number": c["telefono"]}
        }
        client_id = add_entry(CLIENTES_DB_ID, props)
        if client_id:
            print(f"   ✓ {c['nombre']}")
            cliente_ids.append({"id": client_id, "nombre": c["nombre"]})
        time.sleep(0.3)
    
    return cliente_ids

# ============================================
# CARGAR PROVEEDORES
# ============================================
def load_proveedores():
    print("\n🏢 Cargando proveedores de ejemplo...")
    
    proveedores = [
        {"nombre": "Paneles Argentina", "categoria": ["Paneles"], "email": "ventas@panelesarg.com"},
        {"nombre": "Inversores Tech", "categoria": ["Inversores"], "email": "info@inversorestech.com"},
        {"nombre": "Estructuras Metalicas SA", "categoria": ["Estructuras"], "email": "ventas@estructurasmet.com"},
        {"nombre": "Cables y Conectores SRL", "categoria": ["Cables"], "email": "contacto@cablesycon.com"},
        {"nombre": "Transporte Rápido", "categoria": ["Transporte"], "email": "logistica@transporterapido.com"},
        {"nombre": "Electricistas del Sur", "categoria": ["Mano de Obra"], "email": "servicios@elecdelsur.com"},
    ]
    
    proveedor_ids = []
    for p in proveedores:
        props = {
            "Nombre": {"title": [{"text": {"content": p["nombre"]}}]},
            "Categoría": {"multi_select": [{"name": cat} for cat in p["categoria"]]},
            "Email": {"email": p["email"]}
        }
        prov_id = add_entry(PROVEEDORES_DB_ID, props)
        if prov_id:
            print(f"   ✓ {p['nombre']}")
            proveedor_ids.append({"id": prov_id, "nombre": p["nombre"]})
        time.sleep(0.3)
    
    return proveedor_ids

# ============================================
# CARGAR PROYECTOS
# ============================================
def load_proyectos(cliente_ids):
    print("\n🏗️ Cargando proyectos de ejemplo...")
    
    # Obtener IDs de centros de costo
    cc_solar = get_centro_costo_id(100)
    cc_acs = get_centro_costo_id(110)
    cc_piletas = get_centro_costo_id(120)
    cc_consultoria = get_centro_costo_id(130)
    
    today = datetime.now()
    
    proyectos = [
        {"nombre": "Instalación 10kWp - Casa Pérez", "cliente_idx": 0, "cc": cc_solar, "estado": "En Ejecución", "monto": 5500000, "dias_inicio": -15, "dias_fin": 15},
        {"nombre": "Sistema ACS - Hotel del Sol", "cliente_idx": 1, "cc": cc_acs, "estado": "Aprobado", "monto": 3200000, "dias_inicio": 5, "dias_fin": 35},
        {"nombre": "Planta FV 50kWp - Constructora Norte", "cliente_idx": 3, "cc": cc_solar, "estado": "En Ejecución", "monto": 25000000, "dias_inicio": -30, "dias_fin": 30},
        {"nombre": "Climatización Pileta - García", "cliente_idx": 2, "cc": cc_piletas, "estado": "Cotización", "monto": 1800000, "dias_inicio": 10, "dias_fin": 25},
        {"nombre": "Consultoría Eficiencia Energética - Municipalidad", "cliente_idx": 4, "cc": cc_consultoria, "estado": "Finalizado", "monto": 800000, "dias_inicio": -60, "dias_fin": -30},
        {"nombre": "Sistema FV 5kWp - Familia Rodríguez", "cliente_idx": 0, "cc": cc_solar, "estado": "Finalizado", "monto": 2800000, "dias_inicio": -90, "dias_fin": -60},
    ]
    
    proyecto_ids = []
    for p in proyectos:
        props = {
            "Nombre": {"title": [{"text": {"content": p["nombre"]}}]},
            "Estado": {"select": {"name": p["estado"]}},
            "Monto Contrato": {"number": p["monto"]},
            "Fecha Inicio": {"date": {"start": format_date(today + timedelta(days=p["dias_inicio"]))}},
            "Fecha Fin Estimada": {"date": {"start": format_date(today + timedelta(days=p["dias_fin"]))}}
        }
        
        if cliente_ids and p["cliente_idx"] < len(cliente_ids):
            props["Cliente"] = {"relation": [{"id": cliente_ids[p["cliente_idx"]]["id"]}]}
        
        if p["cc"]:
            props["Centro de Costo"] = {"relation": [{"id": p["cc"]}]}
        
        proj_id = add_entry(PROYECTOS_DB_ID, props)
        if proj_id:
            print(f"   ✓ {p['nombre']} ({p['estado']}) - ${p['monto']:,}")
            proyecto_ids.append({"id": proj_id, "nombre": p["nombre"], "monto": p["monto"]})
        time.sleep(0.3)
    
    return proyecto_ids

# ============================================
# CARGAR CUENTAS POR COBRAR
# ============================================
def load_cuentas_por_cobrar(cliente_ids, proyecto_ids):
    print("\n📤 Cargando cuentas por cobrar de ejemplo...")
    
    cc_solar = get_centro_costo_id(100)
    cc_acs = get_centro_costo_id(110)
    cc_consultoria = get_centro_costo_id(130)
    
    today = datetime.now()
    
    cuentas = [
        # Proyecto 1 - Casa Pérez
        {"concepto": "Anticipo Instalación 10kWp", "cliente_idx": 0, "proyecto_idx": 0, "cc": cc_solar, "tipo": "Anticipo", "monto": 2750000, "estado": "Cobrado", "dias_emision": -15, "dias_venc": -10, "dias_cobro": -12},
        {"concepto": "Saldo Final Instalación 10kWp", "cliente_idx": 0, "proyecto_idx": 0, "cc": cc_solar, "tipo": "Saldo Final", "monto": 2750000, "estado": "Pendiente", "dias_emision": -2, "dias_venc": 15, "dias_cobro": None},
        
        # Proyecto 2 - Hotel del Sol
        {"concepto": "Anticipo ACS Hotel del Sol", "cliente_idx": 1, "proyecto_idx": 1, "cc": cc_acs, "tipo": "Anticipo", "monto": 1600000, "estado": "Pendiente", "dias_emision": -5, "dias_venc": 10, "dias_cobro": None},
        
        # Proyecto 3 - Constructora Norte
        {"concepto": "Anticipo 30% Planta FV 50kWp", "cliente_idx": 3, "proyecto_idx": 2, "cc": cc_solar, "tipo": "Anticipo", "monto": 7500000, "estado": "Cobrado", "dias_emision": -30, "dias_venc": -25, "dias_cobro": -26},
        {"concepto": "Cuota 2 Planta FV 50kWp", "cliente_idx": 3, "proyecto_idx": 2, "cc": cc_solar, "tipo": "Cuota", "monto": 7500000, "estado": "Vencido", "dias_emision": -15, "dias_venc": -5, "dias_cobro": None},
        {"concepto": "Saldo Final Planta FV 50kWp", "cliente_idx": 3, "proyecto_idx": 2, "cc": cc_solar, "tipo": "Saldo Final", "monto": 10000000, "estado": "Pendiente", "dias_emision": 0, "dias_venc": 30, "dias_cobro": None},
        
        # Proyecto 5 - Consultoría Municipalidad
        {"concepto": "Honorarios Consultoría EE", "cliente_idx": 4, "proyecto_idx": 4, "cc": cc_consultoria, "tipo": "Honorarios", "monto": 800000, "estado": "Cobrado", "dias_emision": -45, "dias_venc": -30, "dias_cobro": -32},
        
        # Proyecto 6 - Familia Rodríguez
        {"concepto": "Total Sistema FV 5kWp", "cliente_idx": 0, "proyecto_idx": 5, "cc": cc_solar, "tipo": "Saldo Final", "monto": 2800000, "estado": "Cobrado", "dias_emision": -65, "dias_venc": -60, "dias_cobro": -58},
    ]
    
    for c in cuentas:
        props = {
            "Concepto": {"title": [{"text": {"content": c["concepto"]}}]},
            "Tipo Cobro": {"select": {"name": c["tipo"]}},
            "Monto": {"number": c["monto"]},
            "Estado": {"select": {"name": c["estado"]}},
            "Fecha Emisión": {"date": {"start": format_date(today + timedelta(days=c["dias_emision"]))}},
            "Fecha Vencimiento": {"date": {"start": format_date(today + timedelta(days=c["dias_venc"]))}}
        }
        
        if c["dias_cobro"]:
            props["Fecha Cobro"] = {"date": {"start": format_date(today + timedelta(days=c["dias_cobro"]))}}
        
        if cliente_ids and c["cliente_idx"] < len(cliente_ids):
            props["Cliente"] = {"relation": [{"id": cliente_ids[c["cliente_idx"]]["id"]}]}
        
        if proyecto_ids and c["proyecto_idx"] < len(proyecto_ids):
            props["Proyecto"] = {"relation": [{"id": proyecto_ids[c["proyecto_idx"]]["id"]}]}
        
        if c["cc"]:
            props["Centro de Costo"] = {"relation": [{"id": c["cc"]}]}
        
        if add_entry(CXC_DB_ID, props):
            estado_icon = "✅" if c["estado"] == "Cobrado" else ("🔴" if c["estado"] == "Vencido" else "⏳")
            print(f"   {estado_icon} {c['concepto']} - ${c['monto']:,} ({c['estado']})")
        time.sleep(0.3)

# ============================================
# CARGAR CUENTAS POR PAGAR
# ============================================
def load_cuentas_por_pagar(proveedor_ids, proyecto_ids):
    print("\n📥 Cargando cuentas por pagar de ejemplo...")
    
    cc_solar = get_centro_costo_id(100)
    cc_operaciones = get_centro_costo_id(220)
    cc_admin = get_centro_costo_id(240)
    
    today = datetime.now()
    
    cuentas = [
        # Materiales para proyectos
        {"concepto": "Paneles 10kWp - Casa Pérez", "proveedor_idx": 0, "proyecto_idx": 0, "cc": cc_solar, "categoria": "Materiales", "monto": 2200000, "estado": "Pagado", "dias_factura": -20, "dias_venc": -5, "dias_pago": -6},
        {"concepto": "Inversor 10kW - Casa Pérez", "proveedor_idx": 1, "proyecto_idx": 0, "cc": cc_solar, "categoria": "Materiales", "monto": 850000, "estado": "Pendiente", "dias_factura": -10, "dias_venc": 5, "dias_pago": None},
        {"concepto": "Estructura Montaje - Casa Pérez", "proveedor_idx": 2, "proyecto_idx": 0, "cc": cc_solar, "categoria": "Materiales", "monto": 350000, "estado": "Pagado", "dias_factura": -18, "dias_venc": -3, "dias_pago": -4},
        
        {"concepto": "Paneles 50kWp - Constructora Norte", "proveedor_idx": 0, "proyecto_idx": 2, "cc": cc_solar, "categoria": "Materiales", "monto": 9500000, "estado": "Pagado", "dias_factura": -35, "dias_venc": -20, "dias_pago": -22},
        {"concepto": "Inversores Planta 50kWp", "proveedor_idx": 1, "proyecto_idx": 2, "cc": cc_solar, "categoria": "Materiales", "monto": 4200000, "estado": "Vencido", "dias_factura": -25, "dias_venc": -10, "dias_pago": None},
        {"concepto": "Cables y Conectores Planta 50kWp", "proveedor_idx": 3, "proyecto_idx": 2, "cc": cc_solar, "categoria": "Materiales", "monto": 650000, "estado": "Pendiente", "dias_factura": -5, "dias_venc": 10, "dias_pago": None},
        
        # Mano de obra
        {"concepto": "Instalación Eléctrica - Casa Pérez", "proveedor_idx": 5, "proyecto_idx": 0, "cc": cc_solar, "categoria": "Mano de Obra", "monto": 450000, "estado": "Pendiente", "dias_factura": -3, "dias_venc": 12, "dias_pago": None},
        {"concepto": "Instalación Planta 50kWp - Avance", "proveedor_idx": 5, "proyecto_idx": 2, "cc": cc_solar, "categoria": "Mano de Obra", "monto": 1800000, "estado": "Pagado", "dias_factura": -20, "dias_venc": -5, "dias_pago": -6},
        
        # Transporte
        {"concepto": "Flete Paneles a Córdoba", "proveedor_idx": 4, "proyecto_idx": 2, "cc": cc_operaciones, "categoria": "Transporte", "monto": 280000, "estado": "Pagado", "dias_factura": -30, "dias_venc": -15, "dias_pago": -16},
        
        # Gastos fijos (sin proyecto)
        {"concepto": "Sueldos Diciembre 2025", "proveedor_idx": None, "proyecto_idx": None, "cc": cc_admin, "categoria": "Sueldos", "monto": 2500000, "estado": "Pagado", "dias_factura": -35, "dias_venc": -30, "dias_pago": -30},
        {"concepto": "Sueldos Enero 2026", "proveedor_idx": None, "proyecto_idx": None, "cc": cc_admin, "categoria": "Sueldos", "monto": 2500000, "estado": "Pendiente", "dias_factura": -5, "dias_venc": 0, "dias_pago": None},
        {"concepto": "Alquiler Oficina Enero", "proveedor_idx": None, "proyecto_idx": None, "cc": cc_admin, "categoria": "Alquiler", "monto": 450000, "estado": "Pagado", "dias_factura": -10, "dias_venc": -5, "dias_pago": -5},
        {"concepto": "Servicios Contables", "proveedor_idx": None, "proyecto_idx": None, "cc": cc_admin, "categoria": "Servicios", "monto": 180000, "estado": "Pendiente", "dias_factura": -2, "dias_venc": 13, "dias_pago": None},
    ]
    
    for c in cuentas:
        props = {
            "Concepto": {"title": [{"text": {"content": c["concepto"]}}]},
            "Categoría": {"select": {"name": c["categoria"]}},
            "Monto": {"number": c["monto"]},
            "Estado": {"select": {"name": c["estado"]}},
            "Fecha Factura": {"date": {"start": format_date(today + timedelta(days=c["dias_factura"]))}},
            "Fecha Vencimiento": {"date": {"start": format_date(today + timedelta(days=c["dias_venc"]))}}
        }
        
        if c["dias_pago"]:
            props["Fecha Pago"] = {"date": {"start": format_date(today + timedelta(days=c["dias_pago"]))}}
        
        if proveedor_ids and c["proveedor_idx"] is not None and c["proveedor_idx"] < len(proveedor_ids):
            props["Proveedor"] = {"relation": [{"id": proveedor_ids[c["proveedor_idx"]]["id"]}]}
        
        if proyecto_ids and c["proyecto_idx"] is not None and c["proyecto_idx"] < len(proyecto_ids):
            props["Proyecto"] = {"relation": [{"id": proyecto_ids[c["proyecto_idx"]]["id"]}]}
        
        if c["cc"]:
            props["Centro de Costo"] = {"relation": [{"id": c["cc"]}]}
        
        if add_entry(CXP_DB_ID, props):
            estado_icon = "✅" if c["estado"] == "Pagado" else ("🔴" if c["estado"] == "Vencido" else "⏳")
            print(f"   {estado_icon} {c['concepto']} - ${c['monto']:,} ({c['estado']})")
        time.sleep(0.3)

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 60)
    print("📊 CARGANDO DATOS DE EJEMPLO EN EL ERP")
    print("=" * 60)
    
    # Cargar datos en orden
    cliente_ids = load_clientes()
    time.sleep(1)
    
    proveedor_ids = load_proveedores()
    time.sleep(1)
    
    proyecto_ids = load_proyectos(cliente_ids)
    time.sleep(1)
    
    load_cuentas_por_cobrar(cliente_ids, proyecto_ids)
    time.sleep(1)
    
    load_cuentas_por_pagar(proveedor_ids, proyecto_ids)
    
    print("\n" + "=" * 60)
    print("✅ DATOS DE EJEMPLO CARGADOS EXITOSAMENTE")
    print("=" * 60)
    print("\nResumen:")
    print(f"   👥 Clientes: {len(cliente_ids)}")
    print(f"   🏢 Proveedores: {len(proveedor_ids)}")
    print(f"   🏗️ Proyectos: {len(proyecto_ids)}")
    print("   📤 Cuentas por Cobrar: 8")
    print("   📥 Cuentas por Pagar: 13")
    print("\n¡Ahora podés crear los gráficos en el Dashboard!")

if __name__ == "__main__":
    main()
