import json
import requests
import sys
import io
import re
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración (Hardcoded to ensure stability during refactor)
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
    tokens = original_line.split()
    if not tokens: return "S/N"
    
    # Candidatos: tokens que son números puros de ~6 digitos
    for token in reversed(tokens):
        clean_token = token.replace(".", "")
        if clean_token.isdigit() and len(clean_token) >= 4 and len(clean_token) <= 8:
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
    title_content = coupon
    
    monto = abs(mov['monto'])
    fecha = mov['fecha'] 
    
    try:
        dt = datetime.strptime(fecha, "%d-%m-%y")
        fecha_iso = dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
             dt = datetime.strptime(fecha, "%d-%m-%Y")
             fecha_iso = dt.strftime("%Y-%m-%d")
        except:
             fecha_iso = datetime.now().strftime("%Y-%m-%d")


    # Moneda y Monto
    monto_props = {}
    
    # Lógica Exclusiva: O va en Dólares O va en Pesos (según pedido usuario)
    if mov.get('moneda') == 'USD':
        monto_props["Monto Dolares"] = {"number": monto}
        monto_props["Monto"] = {"number": 0} # Explicit 0 for ARS column to avoid issues
    else:
        monto_props["Monto"] = {"number": monto}
        
    # Concepto y Banco
    banco = mov.get('banco', 'DESCONOCIDO').upper()
    concepto_name = "Tarjeta de Crédito" # Default
    if "GALICIA" in banco:
        concepto_name = "T VISA GALICIA"
    elif "BBVA" in banco:
        concepto_name = "T VISA BBVA"
    elif "MACRO" in banco:
        concepto_name = "T VISA MACRO"

    # Payload Notion
    props = {
        # Título: Factura n° (con símbolo de grado)
        "Factura n°": {
            "title": [{"text": {"content": title_content}}]
        },
        **monto_props,
         "Fecha Factura": {
            "date": {"start": fecha_iso}
        },
        "Estado": {
            "select": {"name": "Pendiente"}
        },
        # Concepto: Según Banco
        "Concepto": {
             "select": {"name": concepto_name}
        },
        # Categoría: "Servicios"
        "Categoría": {
             "select": {"name": "Servicios"} 
        },
        # Método de Pago: "Método Pago"
        "Método Pago": {
             "multi_select": [{"name": f"T VISA {banco}"}] # Opcional: ajustar si tienes nombres específicos de métodos de pago
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
    # Asumimos que se corre desde root, o que el json está en root
    json_file = "extracted_movements.json"
    if not 0:
         # Intento buscar en ../ si estoy dentro de src/notion (caso raro de ejecución directa dsd carpeta)
         if not 0: pass

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            movements = json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo {json_file}")
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

