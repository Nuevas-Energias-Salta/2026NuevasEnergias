"""
Script para crear el ERP en Notion
Crea las bases de datos: Centros de Costo, Clientes, Proveedores, Proyectos, CxC, CxP
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


# Configuración
config.NOTION_TOKEN
PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def create_database(parent_id, title, properties, icon="📊"):
    """Crea una base de datos en Notion"""
    url = f"{BASE_URL}/databases"
    
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "icon": {"type": "emoji", "emoji": icon},
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Base de datos '{title}' creada exitosamente!")
        return response.json()
    else:
        print(f"❌ Error creando '{title}': {response.status_code}")
        print(response.text)
        return None

def add_database_entry(database_id, properties):
    """Agrega una entrada a una base de datos"""
    url = f"{BASE_URL}/pages"
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.status_code == 200

def update_database_properties(database_id, new_properties):
    """Actualiza las propiedades de una base de datos existente"""
    url = f"{BASE_URL}/databases/{database_id}"
    
    payload = {"properties": new_properties}
    
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.status_code == 200

# ============================================
# 1. BASE DE DATOS: CENTROS DE COSTO
# ============================================
def create_centros_de_costo():
    print("\n🏷️ Creando base de datos: Centros de Costo...")
    
    properties = {
        "Nombre": {"title": {}},
        "Código": {"number": {"format": "number"}},
        "Tipo": {
            "select": {
                "options": [
                    {"name": "Resultado", "color": "green"},
                    {"name": "Soporte", "color": "blue"}
                ]
            }
        },
        "Descripción": {"rich_text": {}},
        "Activo": {"checkbox": {}}
    }
    
    db = create_database(PAGE_ID, "Centros de Costo", properties, "🏷️")
    
    if db:
        db_id = db["id"]
        print("   Cargando centros de costo...")
        
        # Centros de costo tipo Resultado
        centros_resultado = [
            (100, "Solar Fotovoltaico"),
            (110, "ACS (Agua Caliente Sanitaria)"),
            (120, "Climatización Piletas"),
            (130, "Consultoría (EE / Huella / Capacitaciones)"),
            (140, "Monitoreo & Gestoría Energética (Abonos / Reportes)"),
            (150, "Luminaria Solar"),
            (160, "Calefacción Eléctrica"),
            (170, "Biomasa"),
            (180, "Ingeniería Facturable"),
        ]
        
        # Centros de costo tipo Soporte
        centros_soporte = [
            (200, "Comercial & Marketing"),
            (210, "Ingeniería / Anteproyecto (Preventa NO facturable)"),
            (220, "Operaciones & Logística"),
            (230, "Postventa / O&M (no recurrente)"),
            (240, "Administración & Finanzas"),
            (250, "IT & Automatizaciones (IA / Sistemas)"),
            (260, "Dirección"),
            (270, "General / No asignado (temporal)"),
        ]
        
        for codigo, nombre in centros_resultado:
            props = {
                "Nombre": {"title": [{"text": {"content": nombre}}]},
                "Código": {"number": codigo},
                "Tipo": {"select": {"name": "Resultado"}},
                "Activo": {"checkbox": True}
            }
            if add_database_entry(db_id, props):
                print(f"   ✓ {codigo} - {nombre}")
            time.sleep(0.3)  # Rate limiting
        
        for codigo, nombre in centros_soporte:
            props = {
                "Nombre": {"title": [{"text": {"content": nombre}}]},
                "Código": {"number": codigo},
                "Tipo": {"select": {"name": "Soporte"}},
                "Activo": {"checkbox": True}
            }
            if add_database_entry(db_id, props):
                print(f"   ✓ {codigo} - {nombre}")
            time.sleep(0.3)
        
        return db_id
    return None

# ============================================
# 2. BASE DE DATOS: CLIENTES
# ============================================
def create_clientes():
    print("\n👥 Creando base de datos: Clientes...")
    
    properties = {
        "Nombre": {"title": {}},
        "CUIT": {"rich_text": {}},
        "Contacto": {"rich_text": {}},
        "Email": {"email": {}},
        "Teléfono": {"phone_number": {}},
        "Dirección": {"rich_text": {}},
        "Tipo": {
            "select": {
                "options": [
                    {"name": "Particular", "color": "blue"},
                    {"name": "Empresa", "color": "purple"},
                    {"name": "Organismo Público", "color": "orange"}
                ]
            }
        },
        "Notas": {"rich_text": {}}
    }
    
    db = create_database(PAGE_ID, "Clientes", properties, "👥")
    return db["id"] if db else None

# ============================================
# 3. BASE DE DATOS: PROVEEDORES
# ============================================
def create_proveedores():
    print("\n🏢 Creando base de datos: Proveedores...")
    
    properties = {
        "Nombre": {"title": {}},
        "CUIT": {"rich_text": {}},
        "Contacto": {"rich_text": {}},
        "Email": {"email": {}},
        "Teléfono": {"phone_number": {}},
        "Categoría": {
            "multi_select": {
                "options": [
                    {"name": "Paneles", "color": "yellow"},
                    {"name": "Inversores", "color": "orange"},
                    {"name": "Estructuras", "color": "brown"},
                    {"name": "Cables", "color": "gray"},
                    {"name": "Mano de Obra", "color": "blue"},
                    {"name": "Transporte", "color": "purple"},
                    {"name": "Servicios Profesionales", "color": "pink"},
                    {"name": "Otros", "color": "default"}
                ]
            }
        },
        "Notas": {"rich_text": {}}
    }
    
    db = create_database(PAGE_ID, "Proveedores", properties, "🏢")
    return db["id"] if db else None

# ============================================
# 4. BASE DE DATOS: PROYECTOS/OBRAS
# ============================================
def create_proyectos(clientes_db_id, centros_db_id):
    print("\n🏗️ Creando base de datos: Proyectos/Obras...")
    
    properties = {
        "Nombre": {"title": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Cotización", "color": "gray"},
                    {"name": "Aprobado", "color": "blue"},
                    {"name": "En Ejecución", "color": "yellow"},
                    {"name": "Finalizado", "color": "green"},
                    {"name": "Cancelado", "color": "red"}
                ]
            }
        },
        "Monto Contrato": {"number": {"format": "argentine_peso"}},
        "Fecha Inicio": {"date": {}},
        "Fecha Fin Estimada": {"date": {}},
        "Fecha Fin Real": {"date": {}},
        "Potencia kWp": {"number": {"format": "number"}},
        "Ubicación": {"rich_text": {}},
        "Referencia Trello": {"url": {}},
        "Notas": {"rich_text": {}}
    }
    
    # Agregar relaciones si existen las otras BDs
    if clientes_db_id:
        properties["Cliente"] = {"relation": {"database_id": clientes_db_id, "single_property": {}}}
    if centros_db_id:
        properties["Centro de Costo"] = {"relation": {"database_id": centros_db_id, "single_property": {}}}
    
    db = create_database(PAGE_ID, "Proyectos/Obras", properties, "🏗️")
    return db["id"] if db else None

# ============================================
# 5. BASE DE DATOS: CUENTAS POR COBRAR
# ============================================
def create_cuentas_por_cobrar(clientes_db_id, proyectos_db_id, centros_db_id):
    print("\n📤 Creando base de datos: Cuentas por Cobrar...")
    
    properties = {
        "Concepto": {"title": {}},
        "Tipo Cobro": {
            "select": {
                "options": [
                    {"name": "Anticipo", "color": "blue"},
                    {"name": "Cuota", "color": "purple"},
                    {"name": "Saldo Final", "color": "green"},
                    {"name": "Abono Mensual", "color": "orange"},
                    {"name": "Honorarios", "color": "pink"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Número Factura": {"rich_text": {}},
        "Monto": {"number": {"format": "argentine_peso"}},
        "Fecha Emisión": {"date": {}},
        "Fecha Vencimiento": {"date": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Pendiente", "color": "yellow"},
                    {"name": "Cobrado", "color": "green"},
                    {"name": "Vencido", "color": "red"},
                    {"name": "Anulado", "color": "gray"}
                ]
            }
        },
        "Fecha Cobro": {"date": {}},
        "Método Pago": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Cheque", "color": "orange"},
                    {"name": "Mercado Pago", "color": "purple"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Notas": {"rich_text": {}}
    }
    
    # Agregar relaciones
    if clientes_db_id:
        properties["Cliente"] = {"relation": {"database_id": clientes_db_id, "single_property": {}}}
    if proyectos_db_id:
        properties["Proyecto"] = {"relation": {"database_id": proyectos_db_id, "single_property": {}}}
    if centros_db_id:
        properties["Centro de Costo"] = {"relation": {"database_id": centros_db_id, "single_property": {}}}
    
    db = create_database(PAGE_ID, "Cuentas por Cobrar", properties, "📤")
    return db["id"] if db else None

# ============================================
# 6. BASE DE DATOS: CUENTAS POR PAGAR
# ============================================
def create_cuentas_por_pagar(proveedores_db_id, proyectos_db_id, centros_db_id):
    print("\n📥 Creando base de datos: Cuentas por Pagar...")
    
    properties = {
        "Concepto": {"title": {}},
        "Categoría": {
            "select": {
                "options": [
                    {"name": "Materiales", "color": "yellow"},
                    {"name": "Mano de Obra", "color": "blue"},
                    {"name": "Sueldos", "color": "green"},
                    {"name": "Transporte", "color": "purple"},
                    {"name": "Servicios", "color": "pink"},
                    {"name": "Alquiler", "color": "orange"},
                    {"name": "Impuestos", "color": "red"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Número Factura": {"rich_text": {}},
        "Monto": {"number": {"format": "argentine_peso"}},
        "Fecha Factura": {"date": {}},
        "Fecha Vencimiento": {"date": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Pendiente", "color": "yellow"},
                    {"name": "Pagado", "color": "green"},
                    {"name": "Vencido", "color": "red"},
                    {"name": "Anulado", "color": "gray"}
                ]
            }
        },
        "Fecha Pago": {"date": {}},
        "Método Pago": {
            "select": {
                "options": [
                    {"name": "Transferencia", "color": "blue"},
                    {"name": "Efectivo", "color": "green"},
                    {"name": "Cheque", "color": "orange"},
                    {"name": "Débito Automático", "color": "purple"},
                    {"name": "Otro", "color": "gray"}
                ]
            }
        },
        "Notas": {"rich_text": {}}
    }
    
    # Agregar relaciones
    if proveedores_db_id:
        properties["Proveedor"] = {"relation": {"database_id": proveedores_db_id, "single_property": {}}}
    if proyectos_db_id:
        properties["Proyecto"] = {"relation": {"database_id": proyectos_db_id, "single_property": {}}}
    if centros_db_id:
        properties["Centro de Costo"] = {"relation": {"database_id": centros_db_id, "single_property": {}}}
    
    db = create_database(PAGE_ID, "Cuentas por Pagar", properties, "📥")
    return db["id"] if db else None

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 50)
    print("🚀 CREANDO ERP EN NOTION")
    print("=" * 50)
    print(f"Página destino: {PAGE_ID}")
    
    # Crear bases de datos en orden (primero las que no tienen dependencias)
    centros_db_id = create_centros_de_costo()
    time.sleep(1)
    
    clientes_db_id = create_clientes()
    time.sleep(1)
    
    proveedores_db_id = create_proveedores()
    time.sleep(1)
    
    proyectos_db_id = create_proyectos(clientes_db_id, centros_db_id)
    time.sleep(1)
    
    cxc_db_id = create_cuentas_por_cobrar(clientes_db_id, proyectos_db_id, centros_db_id)
    time.sleep(1)
    
    cxp_db_id = create_cuentas_por_pagar(proveedores_db_id, proyectos_db_id, centros_db_id)
    
    print("\n" + "=" * 50)
    print("✅ PROCESO COMPLETADO")
    print("=" * 50)
    print("\nBases de datos creadas:")
    print(f"  🏷️ Centros de Costo: {centros_db_id}")
    print(f"  👥 Clientes: {clientes_db_id}")
    print(f"  🏢 Proveedores: {proveedores_db_id}")
    print(f"  🏗️ Proyectos/Obras: {proyectos_db_id}")
    print(f"  📤 Cuentas por Cobrar: {cxc_db_id}")
    print(f"  📥 Cuentas por Pagar: {cxp_db_id}")
    print("\n¡Revisá tu Notion para ver las bases de datos!")

if __name__ == "__main__":
    main()
