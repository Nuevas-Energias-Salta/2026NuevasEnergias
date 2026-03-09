import requests
import json
import sys
import io
import csv
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410" 
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

def get_text_property(props, name):
    """Extrae texto plano de una propiedad rich_text o title"""
    if name not in props: return ""
    prop = props[name]
    if prop['type'] == 'title' and prop['title']:
        return prop['title'][0]['plain_text']
    elif prop['type'] == 'rich_text' and prop['rich_text']:
        return prop['rich_text'][0]['plain_text']
    return ""

def export_data():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    filename = "verificacion_datos.csv"
    print(f"📄 Generando reporte detallado en: {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['TIPO', 'NOMBRE/CONCEPTO', 'MONTO', 'ESTADO', 'ID NOTION'])
    
        # 1. CxC (Ingresos)
        print("   ⬇️  Descargando Ingresos (CxC)...")
        has_more = True
        next_cursor = None
        count_cxc = 0
        
        while has_more:
            payload = {"page_size": 100}
            if next_cursor: payload["start_cursor"] = next_cursor
            
            res = requests.post(f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query", headers=headers, json=payload)
            if res.status_code != 200:
                print(f"❌ Error CxC: {res.text}")
                break
                
            data = res.json()
            for item in data.get("results", []):
                props = item['properties']
                
                # Nombre (Intenta buscar title 'Nombre' o 'Name' o lo que sea title)
                nombre = get_text_property(props, 'Nombre')
                if not nombre:
                     # Buscar cualquier propiedad title
                    for k, v in props.items():
                        if v['type'] == 'title':
                             nombre = get_text_property(props, k)
                             break
                
                # Monto
                monto = 0
                if "Monto Base" in props and "number" in props["Monto Base"]:
                     monto = props["Monto Base"]["number"] or 0
                
                # Estado
                estado = ""
                if "Estado" in props and "select" in props["Estado"] and props["Estado"]["select"]:
                    estado = props["Estado"]["select"]["name"]
                
                writer.writerow(['INGRESO (CxC)', nombre, f"{monto:.2f}", estado, item['id']])
                count_cxc += 1
            
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

        # 2. CxP (Gastos)
        print("   ⬇️  Descargando Gastos (CxP)...")
        has_more = True
        next_cursor = None
        count_cxp = 0
        
        while has_more:
            payload = {"page_size": 100}
            if next_cursor: payload["start_cursor"] = next_cursor
            
            res = requests.post(f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query", headers=headers, json=payload)
            if res.status_code != 200:
                print(f"❌ Error CxP: {res.text}")
                break
                
            data = res.json()
            for item in data.get("results", []):
                props = item['properties']
                
                # Nombre
                nombre = get_text_property(props, 'Nombre')
                
                # Monto
                monto = 0
                if "Monto" in props and "number" in props["Monto"]:
                     monto = props["Monto"]["number"] or 0
                
                # Estado
                estado = ""
                if "Estado" in props and "select" in props["Estado"] and props["Estado"]["select"]:
                    estado = props["Estado"]["select"]["name"]
                
                writer.writerow(['GASTO (CxP)', nombre, f"{monto:.2f}", estado, item['id']])
                count_cxp += 1
                
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

    print(f"\n✅ Reporte generado exitosamente.")
    print(f"   - {count_cxc} Ingresos exportados")
    print(f"   - {count_cxp} Gastos exportados")
    print(f"   👉 Abre el archivo 'verificacion_datos.csv' en Excel para revisar fila por fila.")

if __name__ == "__main__":
    export_data()

