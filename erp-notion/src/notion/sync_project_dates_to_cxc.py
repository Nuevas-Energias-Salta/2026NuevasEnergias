"""
Script para actualizar las fechas de CxC con las fechas de sus Proyectos relacionados
Fecha Emisión = Fecha Inicio del Proyecto
Fecha Vencimiento = Fecha Fin Estimada del Proyecto (o Inicio + 30 días)
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from datetime import datetime, timedelta
import time

config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def get_all_cxc():
    """Obtiene todas las cuentas por cobrar"""
    print("📤 Obteniendo Cuentas por Cobrar...")
    sys.stdout.flush()
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}/query"
    
    all_cxc = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        try:
            res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                all_cxc.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")
            else:
                print(f"   ❌ Error: {res.status_code}")
                sys.stdout.flush()
                break
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            sys.stdout.flush()
            break
    
    print(f"   ✓ {len(all_cxc)} cuentas encontradas")
    sys.stdout.flush()
    return all_cxc

def get_project_dates(project_id):
    """Obtiene las fechas de un proyecto"""
    url = f"{BASE_URL}/pages/{project_id}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            page = res.json()
            props = page["properties"]
            
            # Obtener Fecha Inicio
            fecha_inicio_prop = props.get("Fecha Inicio", {}).get("date")
            fecha_inicio = None
            if fecha_inicio_prop:
                fecha_inicio = fecha_inicio_prop.get("start")
            
            # Obtener Fecha Fin Estimada
            fecha_fin_prop = props.get("Fecha Fin Estimada", {}).get("date")
            fecha_fin = None
            if fecha_fin_prop:
                fecha_fin = fecha_fin_prop.get("start")
            
            # Si no hay fecha fin, calcular 30 días después de inicio
            if fecha_inicio and not fecha_fin:
                try:
                    dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                    fecha_fin = (dt + timedelta(days=30)).strftime("%Y-%m-%d")
                except:
                    pass
            
            return fecha_inicio, fecha_fin
        else:
            return None, None
    except Exception as e:
        return None, None

def update_cxc_dates(cxc_id, cxc_name, fecha_emision, fecha_vencimiento):
    """Actualiza las fechas de una CxC"""
    url = f"{BASE_URL}/pages/{cxc_id}"
    
    properties = {}
    
    if fecha_emision:
        properties["Fecha Emisión"] = {"date": {"start": fecha_emision}}
    
    if fecha_vencimiento:
        properties["Fecha Vencimiento"] = {"date": {"start": fecha_vencimiento}}
    
    if not properties:
        return False
    
    payload = {"properties": properties}
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"   ✅ {cxc_name[:50]}")
            if fecha_emision:
                print(f"      📅 Emisión: {fecha_emision}")
            if fecha_vencimiento:
                print(f"      📅 Vencimiento: {fecha_vencimiento}")
            sys.stdout.flush()
            return True
        else:
            print(f"   ❌ Error {res.status_code}: {cxc_name[:50]}")
            sys.stdout.flush()
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        sys.stdout.flush()
        return False

def main():
    print("=" * 60)
    print("🔄 ACTUALIZANDO FECHAS DE CXC DESDE PROYECTOS")
    print("=" * 60)
    sys.stdout.flush()
    
    # Obtener todas las CxC
    all_cxc = get_all_cxc()
    if not all_cxc:
        print("\n❌ No se pudieron obtener CxC")
        return
    
    print(f"\n🔄 Procesando {len(all_cxc)} cuentas...\n")
    sys.stdout.flush()
    
    updated = 0
    no_project = 0
    no_dates = 0
    errors = 0
    
    for idx, cxc in enumerate(all_cxc):
        print(f"[{idx+1}/{len(all_cxc)}] ", end="")
        sys.stdout.flush()
        
        try:
            props = cxc["properties"]
            
            # Obtener nombre de la CxC
            concepto_prop = props.get("Concepto", {}).get("title", [])
            concepto = concepto_prop[0].get("text", {}).get("content", "Sin nombre") if concepto_prop else "Sin nombre"
            
            # Obtener proyecto relacionado
            proyecto_prop = props.get("Proyecto", {}).get("relation", [])
            
            if not proyecto_prop:
                print(f"⚠️ Sin proyecto: {concepto[:40]}")
                sys.stdout.flush()
                no_project += 1
                continue
            
            # Obtener ID del proyecto
            proyecto_id = proyecto_prop[0].get("id")
            
            # Obtener fechas del proyecto
            fecha_inicio, fecha_fin = get_project_dates(proyecto_id)
            
            if not fecha_inicio and not fecha_fin:
                print(f"⚠️ Sin fechas en proyecto: {concepto[:40]}")
                sys.stdout.flush()
                no_dates += 1
                continue
            
            # Actualizar CxC
            if update_cxc_dates(cxc["id"], concepto, fecha_inicio, fecha_fin):
                updated += 1
            else:
                errors += 1
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            sys.stdout.flush()
            errors += 1
    
    print("\n" + "=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"   ✅ Actualizados: {updated}")
    print(f"   ⚠️ Sin proyecto: {no_project}")
    print(f"   ⚠️ Sin fechas: {no_dates}")
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
