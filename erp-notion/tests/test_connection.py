import requests
import json
import sys
import io

# Fix encoding issues in Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración# Configuración (CORREGIDA)
# NOTION_TOKEN se mantiene igual
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs Corregidos según find_financial_dbs.py
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410" # Real CxP (Transactions)
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a" # Real CxC (Transactions)
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"

def test_connection():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print(f"🔍 Iniciando prueba de conexión con Token: {NOTION_TOKEN[:10]}...")
    
    # 1. Proyectos
    print(f"\n1️⃣  Consultando Proyectos (DB: {CENTROS_DB_ID})...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{CENTROS_DB_ID}/query"
        res = requests.post(url, headers=headers, json={"page_size": 10})
        if res.status_code == 200:
            data = res.json()
            count = len(data.get("results", []))
            print(f"   ✅ ÉXITO: Se encontraron {count} proyectos/centros")
            for p in data.get("results", [])[:3]:
                # Intentar obtener el título
                props = p.get("properties", {})
                title_prop = next((v for k,v in props.items() if v.get("id") == "title"), None)
                if not title_prop: 
                    # Buscar cualquier propiedad title
                    for k, v in props.items():
                        if v.get("type") == "title":
                            title_prop = v
                            break
                
                title = "Sin título"
                if title_prop and title_prop.get("title"):
                    title = title_prop.get("title")[0].get("plain_text", "Sin título")
                
                print(f"      - {title}")
        else:
            print(f"   ❌ ERROR: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ❌ EXCEPCIÓN: {e}")

    # 2. CxC (Ingresos)
    print(f"\n2️⃣  Consultando CxC (Ingresos) (DB: {CXC_DB_ID})...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query"
        res = requests.post(url, headers=headers, json={"page_size": 100})
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            print(f"   ✅ ÉXITO: Se encontraron {len(results)} items en CxC")
            
            total = 0
            pending = 0
            for r in results:
                props = r.get("properties", {})
                
                # Monto: En CxC se llama "Monto Base"
                monto = 0
                if "Monto Base" in props and "number" in props["Monto Base"]:
                     monto = props["Monto Base"]["number"] or 0
                
                # Estado
                estado = ""
                if "Estado" in props and "select" in props["Estado"] and props["Estado"]["select"]:
                    estado = props["Estado"]["select"]["name"]
                    
                total += monto
                # Simplificación de estados pendientes
                if estado and estado.lower() not in ["pagada", "cobrada", "pagado", "cobrado"]:
                    pending += monto
            
            print(f"   💵 Total Ingresos Calculado: ${total:,.2f}")
            print(f"   🕒 Total Pendiente Calculado: ${pending:,.2f}")
        else:
            print(f"   ❌ ERROR: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ❌ EXCEPCIÓN: {e}")

    # 3. CxP (Gastos)
    print(f"\n3️⃣  Consultando CxP (Gastos) (DB: {CXP_DB_ID})...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query"
        res = requests.post(url, headers=headers, json={"page_size": 100})
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            print(f"   ✅ ÉXITO: Se encontraron {len(results)} items en CxP")
            
            total_gastos = 0
            for r in results:
                props = r.get("properties", {})
                # Monto: En CxP se llama "Monto"
                monto = 0
                if "Monto" in props and "number" in props["Monto"]:
                     monto = props["Monto"]["number"] or 0
                total_gastos += monto
            
            print(f"   💸 Total Gastos Calculado: ${total_gastos:,.2f}")
        else:
            print(f"   ❌ ERROR: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ❌ EXCEPCIÓN: {e}")

if __name__ == "__main__":
    test_connection()

