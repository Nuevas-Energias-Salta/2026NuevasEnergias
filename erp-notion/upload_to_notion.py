import json
import requests
import sys
import io
import re
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"
PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Cache local para no consultar Notion repetidamente por le mismo proveedor en esta ejecución
vendor_cache = {}

def get_or_create_vendor(name):
    """Busca un proveedor por nombre, si no existe lo crea. Retorna el ID."""
    name = name.strip()
    if not name: return None
    
    # 1. Chequear cache
    if name in vendor_cache:
        return vendor_cache[name]
    
    # 2. Buscar en Notion
    url_query = f"https://api.notion.com/v1/databases/{PROVEEDORES_DB_ID}/query"
    payload = {
        "filter": {
            "property": "Nombre", 
            "title": {
                "equals": name
            }
        }
    }
    try:
        res = requests.post(url_query, headers=HEADERS, json=payload)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                vendor_id = results[0]["id"]
                vendor_cache[name] = vendor_id
                return vendor_id
        else:
            print(f"   ⚠️ Error buscando proveedor: {res.text}")
    except Exception as e:
        print(f"   ⚠️ Excepción buscando proveedor: {e}")

    # 3. Crear si no existe
    print(f"   ✨ Creando nuevo proveedor: '{name}'...")
    url_create = "https://api.notion.com/v1/pages"
    payload_create = {
        "parent": {"database_id": PROVEEDORES_DB_ID},
        "properties": {
            "Nombre": {
                "title": [{"text": {"content": name}}]
            },
            # Corregido: Categoría en Proveedores es multi_select (list)
            "Categoría": {"multi_select": [{"name": "Otros"}]} 
        }
    }
    try:
        res = requests.post(url_create, headers=HEADERS, json=payload_create)
        if res.status_code == 200:
            vendor_id = res.json()["id"]
            vendor_cache[name] = vendor_id
            return vendor_id
        else:
            print(f"   ❌ Error creando proveedor: {res.text}")
            return None
    except Exception as e:
        print(f"   ❌ Excepción creando proveedor: {e}")
        return None

def clean_vendor_name(text):
    """Limpia prefijos comunes y detecta impuestos"""
    
    uc_text = text.upper()
    
    # 1. Detectar Impuestos / Items Internos
    tax_keywords = [
        "SU PAGO EN", "IMPUESTO", "DB IVA", "PERCEP", 
        "COMISION", "MANT. DE CUENTA", "COMISIÓN"
    ]
    for kw in tax_keywords:
        if kw in uc_text:
            return "Impuestos", True # Nombre, EsImpuesto
            
    # 2. Limpieza de Prefijos
    prefixes = [
        r"merpago\*", r"mp\*", r"mercado\s*pago\*", r"\*\s*merpago\*",
        r"payu\*", r"dlocal\*", r"payulatam\*", r"dlo\*",
        r"google\s*\*", r"openai\s*\*", r"trello\.com\*",
        r"\*\s+" # Asterisco + espacio al inicio (ej "* NEUMATICOS")
    ]
    
    cleaned = text
    for p in prefixes:
        # Reemplazar prefijo al inicio, ignorando mayus/minus
        cleaned = re.sub(f"^{p}", "", cleaned, flags=re.IGNORECASE)
        
    return cleaned.strip(), False

def extract_coupon(original_line):
    """Intenta extraer el número de comprobante/cupón de la línea original"""
    # Patrones comunes de cupón en los ejemplos:
    # Galicia: "005365" (6 digitos al final antes del monto), "322263"
    # BBVA: "858124", "005902", "C.06/06"
    
    # Estrategia: Buscar secuencia de 6 dígitos que NO sea fecha
    # O buscar tokens numéricos entre la descripción y los montos finales
    
    tokens = original_line.split()
    if not tokens: return "S/N"
    
    # Candidatos: tokens que son números puros de ~6 digitos
    for token in reversed(tokens):
        # Limpiar puntos si es necesario?
        clean_token = token.replace(".", "")
        if clean_token.isdigit() and len(clean_token) >= 4 and len(clean_token) <= 8:
            # Descartar si parece un año o fecha (ej 2026, 01) - Aunque 2026 podría ser cupon
            # Descartar si parece monto (ya procesado, pero aquí estamos viendo raw tokens)
            return token
            
    # Fallback: Buscar "C.XX/XX"
    match = re.search(r'C\.\d{2}/\d{2}', original_line)
    if match:
        return match.group(0)
        
    return "S/N"

def upload_movement(mov):
    """Sube un movimiento individual a Notion"""
    
    # Limpiar descripción y detectar si es impuesto
    vendor_name, is_tax = clean_vendor_name(mov['descripcion'])
    
    # Obtener o crear proveedor (Si es impuesto, proveedor="Impuestos")
    vendor_id = get_or_create_vendor(vendor_name)
    
    # Extraer Cupón para usar como Título (Factura n)
    coupon = extract_coupon(mov['original'])
    # Título: Coupon
    title_content = coupon
    
    monto = abs(mov['monto'])
    fecha = mov['fecha'] 
    
    try:
        # Si viene como DD-MM-YY (ej 05-01-26)
        dt = datetime.strptime(fecha, "%d-%m-%y")
        fecha_iso = dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
             dt = datetime.strptime(fecha, "%d-%m-%Y")
             fecha_iso = dt.strftime("%Y-%m-%d")
        except:
             fecha_iso = datetime.now().strftime("%Y-%m-%d")

    # Payload Notion
    props = {
        # Título: Factura n (Schema: title)
        "Factura n": {
            "title": [{"text": {"content": title_content}}]
        },
        "Monto": {
            "number": monto
        },
         "Fecha Factura": {
            "date": {"start": fecha_iso}
        },
        "Estado": {
            "select": {"name": "Pendiente"}
        },
        # Concepto: "Tarjeta de Crédito" (Schema: select)
        "Concepto": {
             "select": {"name": "Tarjeta de Crédito"}
        },
        # Categoría: "Servicios" (Schema: select)
        "Categoría": {
             "select": {"name": "Servicios"} 
        },
        # Método de Pago: "T VISA 1768" (Schema: multi_select, key="Mtodo Pago")
        "Mtodo Pago": {
             "multi_select": [{"name": "T VISA 1768"}]
        }
    }
    
    # Agregar relación con proveedor
    if vendor_id:
        props["Proveedor"] = {"relation": [{"id": vendor_id}]}

    data = {
        "parent": {"database_id": CXP_DB_ID},
        "properties": props
    }
    
    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
        if res.status_code == 200:
            return True, ""
        else:
            return False, f"{res.status_code} - {res.text}"
    except Exception as e:
        return False, str(e)

def main():
    json_file = "extracted_movements.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            movements = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró el archivo de movimientos extraídos.")
        return

    print(f"📦 Cargando {len(movements)} movimientos a Notion...")
    
    success_count = 0
    error_count = 0
    
    for i, mov in enumerate(movements):
        nome_display = clean_vendor_name(mov['descripcion'])[0]
        print(f"   [{i+1}/{len(movements)}] {nome_display} (Cupon: {extract_coupon(mov['original'])})... ", end="", flush=True)
        ok, msg = upload_movement(mov)
        if ok:
            print("✅")
            success_count += 1
        else:
            print(f"❌ Error: {msg}")
            error_count += 1
            
    print(f"\nResumen: {success_count} subidos, {error_count} fallidos.")

if __name__ == "__main__":
    main()

