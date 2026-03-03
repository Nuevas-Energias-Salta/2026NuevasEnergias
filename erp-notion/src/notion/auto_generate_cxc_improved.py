"""
Script mejorado para auto-generar Cuentas por Cobrar desde los Proyectos.
Incluye: verificación de duplicados, generación de cuotas parciales, mejor validación.
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from datetime import datetime, timedelta

# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

# IDs de bases de datos específicas
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

# Configuración de generación (ahora desde config central)
CONFIG = config.CXC_CONFIG

def get_all_projects():
    """Obtiene todos los proyectos con paginación"""
    print("📂 Leyendo proyectos de Notion...")
    url = f"{config.NOTION_BASE_URL}/databases/{PROYECTOS_DB_ID}/query"
    
    projects = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor: payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=config.get_notion_headers(), json=payload)
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

def check_existing_cxc(proyecto_id):
    """Verifica si ya existen cuentas por cobrar para un proyecto"""
    url = f"{BASE_URL}/databases/{CXC_DB_ID}/query"
    
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

def create_cxc_entry(proyecto, tipo, concepto, monto, fecha_emision, dias_vencimiento):
    """Crea una entrada de cuenta por cobrar"""
    try:
        props = proyecto["properties"]
        
        # Cliente
        cliente_rel = props.get("Cliente", {}).get("relation", [])
        if not cliente_rel:
            return None, "Sin cliente"
        cliente_id = cliente_rel[0]["id"]
        
        # Centro de Costo
        cc_rel = props.get("Centro de Costo", {}).get("relation", [])
        cc_id = cc_rel[0]["id"] if cc_rel else None
        
        # Estado del proyecto
        estado = props.get("Estado", {}).get("select", {}).get("name", "")
        
        # Decidir estado de la cuenta
        if estado == "Finalizado":
            cuenta_estado = "Cobrado"
        elif estado == "Cancelado":
            return None, "Proyecto cancelado"
        else:
            cuenta_estado = "Pendiente"
        
        fecha_vencimiento = fecha_emision + timedelta(days=dias_vencimiento)
        
        # Payload
        cxc_props = {
            "Concepto": {"title": [{"text": {"content": concepto}}]},
            "Cliente": {"relation": [{"id": cliente_id}]},
            "Proyecto": {"relation": [{"id": proyecto["id"]}]},
            "Monto": {"number": round(monto, 2)},
            "Estado": {"select": {"name": cuenta_estado}},
            "Tipo Cobro": {"select": {"name": tipo}},
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

def generate_partial_payments(proyecto):
    """Genera cuentas con cuotas parciales (anticipo + cuotas + saldo)"""
    try:
        props = proyecto["properties"]
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin nombre")
        monto = props.get("Monto Contrato", {}).get("number")
        
        if not monto or monto <= 0:
            return 0, "Sin monto"
        
        # Verificar duplicados
        existe, cuenta_existente = check_existing_cxc(proyecto["id"])
        if existe:
            return 0, f"Ya tiene {cuenta_existente} cuenta(s)"
        
        today = datetime.now()
        created = 0
        
        # 1. Anticipo
        monto_anticipo = monto * CONFIG["anticipo_porcentaje"]
        result, msg = create_cxc_entry(
            proyecto, "Anticipo", 
            f"Anticipo - {nombre}",
            monto_anticipo, 
            today, 
            CONFIG["dias_vencimiento_anticipo"]
        )
        if result:
            created += 1
            print(f"      ✓ Anticipo: ${monto_anticipo:,.0f}")
        
        # 2. Cuotas intermedias
        monto_cuotas_total = monto * (1 - CONFIG["anticipo_porcentaje"] - CONFIG["saldo_final_porcentaje"])
        monto_por_cuota = monto_cuotas_total / CONFIG["numero_cuotas"]
        
        for i in range(CONFIG["numero_cuotas"]):
            dias_offset = CONFIG["dias_entre_cuotas"] * (i + 1)
            fecha_cuota = today + timedelta(days=dias_offset)
            
            result, msg = create_cxc_entry(
                proyecto, "Cuota",
                f"Cuota {i+1}/{CONFIG['numero_cuotas']} - {nombre}",
                monto_por_cuota,
                fecha_cuota,
                CONFIG["dias_vencimiento_cuota"]
            )
            if result:
                created += 1
                print(f"      ✓ Cuota {i+1}: ${monto_por_cuota:,.0f}")
        
        # 3. Saldo final
        monto_saldo = monto * CONFIG["saldo_final_porcentaje"]
        fecha_saldo = today + timedelta(days=CONFIG["dias_entre_cuotas"] * (CONFIG["numero_cuotas"] + 1))
        
        result, msg = create_cxc_entry(
            proyecto, "Saldo Final",
            f"Saldo Final - {nombre}",
            monto_saldo,
            fecha_saldo,
            CONFIG["dias_vencimiento_saldo"]
        )
        if result:
            created += 1
            print(f"      ✓ Saldo Final: ${monto_saldo:,.0f}")
        
        return created, f"{created} cuentas creadas"
        
    except Exception as e:
        return 0, f"Error: {str(e)[:50]}"

def generate_single_payment(proyecto):
    """Genera una única cuenta por cobrar por el monto total"""
    try:
        props = proyecto["properties"]
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin nombre")
        monto = props.get("Monto Contrato", {}).get("number")
        
        if not monto or monto <= 0:
            return 0, "Sin monto"
        
        # Verificar duplicados
        existe, cuenta_existente = check_existing_cxc(proyecto["id"])
        if existe:
            return 0, f"Ya tiene {cuenta_existente} cuenta(s)"
        
        today = datetime.now()
        
        result, msg = create_cxc_entry(
            proyecto, "Contrato",
            f"Contrato - {nombre}",
            monto,
            today - timedelta(days=10),
            30
        )
        
        if result:
            return 1, f"${monto:,.0f}"
        else:
            return 0, msg
            
    except Exception as e:
        return 0, f"Error: {str(e)[:50]}"

def main():
    print("=" * 60)
    print("🏗️ AUTO-GENERACIÓN DE CUENTAS POR COBRAR (MEJORADO)")
    print("=" * 60)
    print(f"\n⚙️ Configuración:")
    print(f"   • Generar cuotas: {'Sí' if CONFIG['generar_cuotas'] else 'No'}")
    if CONFIG['generar_cuotas']:
        print(f"   • Anticipo: {CONFIG['anticipo_porcentaje']*100}%")
        print(f"   • Cuotas intermedias: {CONFIG['numero_cuotas']}")
        print(f"   • Saldo final: {CONFIG['saldo_final_porcentaje']*100}%")
    
    projects = get_all_projects()
    
    if not projects:
        print("❌ No hay proyectos para procesar.")
        return
    
    print(f"\n💰 Generando cuentas por cobrar...")
    
    total_created = 0
    skipped = 0
    errors = 0
    
    for project in projects:
        try:
            nombre = project["properties"].get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "?")
        except:
            nombre = "Proyecto sin nombre"
        
        print(f"\n   📋 {nombre}")
        
        if CONFIG["generar_cuotas"]:
            created, msg = generate_partial_payments(project)
        else:
            created, msg = generate_single_payment(project)
        
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

if __name__ == "__main__":
    main()
