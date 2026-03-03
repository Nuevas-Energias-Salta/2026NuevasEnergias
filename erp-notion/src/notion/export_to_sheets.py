"""
Script para exportar datos de Notion a CSVs para Google Sheets
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import csv
import os
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

from datetime import datetime

config.NOTION_TOKEN

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL
OUTPUT_DIR = "exports"

# IDs de bases de datos
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CLIENTES_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"

def get_all_pages(db_id):
    """Obtiene todas las páginas de una base de datos"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    all_pages = []
    has_more = True
    cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        res = requests.post(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            all_pages.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            cursor = data.get("next_cursor")
        else:
            print(f"Error: {res.status_code}")
            break
    
    return all_pages

def extract_property(props, key, default=""):
    """Extrae el valor de una propiedad de Notion"""
    if key not in props:
        return default
    
    prop = props[key]
    prop_type = prop.get("type", "")
    
    try:
        if prop_type == "title":
            return prop["title"][0]["text"]["content"] if prop["title"] else ""
        elif prop_type == "rich_text":
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else ""
        elif prop_type == "number":
            return prop["number"] if prop["number"] is not None else 0
        elif prop_type == "select":
            return prop["select"]["name"] if prop["select"] else ""
        elif prop_type == "date":
            return prop["date"]["start"] if prop["date"] else ""
        elif prop_type == "email":
            return prop["email"] if prop["email"] else ""
        elif prop_type == "phone_number":
            return prop["phone_number"] if prop["phone_number"] else ""
        elif prop_type == "relation":
            return prop["relation"][0]["id"] if prop["relation"] else ""
        elif prop_type == "formula":
            formula_type = prop["formula"].get("type", "")
            if formula_type == "number":
                return prop["formula"]["number"] if prop["formula"]["number"] is not None else 0
            elif formula_type == "string":
                return prop["formula"]["string"] if prop["formula"]["string"] else ""
        elif prop_type == "rollup":
            rollup_type = prop["rollup"].get("type", "")
            if rollup_type == "number":
                return prop["rollup"]["number"] if prop["rollup"]["number"] is not None else 0
    except:
        pass
    
    return default

def export_proyectos():
    """Exporta proyectos a CSV"""
    print("Exportando Proyectos...")
    pages = get_all_pages(PROYECTOS_DB_ID)
    
    filename = os.path.join(OUTPUT_DIR, "proyectos.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nombre", "Cliente", "Estado", "Centro_Costo", "Monto_Contrato", "Fecha_Creacion"])
        
        for page in pages:
            props = page.get("properties", {})
            writer.writerow([
                page["id"],
                extract_property(props, "Nombre"),
                extract_property(props, "Cliente"),
                extract_property(props, "Estado"),
                extract_property(props, "Centro de Costo"),
                extract_property(props, "Monto Contrato", 0),
                page.get("created_time", "")[:10]
            ])
    
    print(f"   Exportados: {len(pages)} proyectos")
    return len(pages)

def export_cxc():
    """Exporta Cuentas por Cobrar a CSV"""
    print("Exportando Cuentas por Cobrar...")
    pages = get_all_pages(CXC_DB_ID)
    
    filename = os.path.join(OUTPUT_DIR, "cxc.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Proyecto", "Cliente", "Monto_Total", "Monto_Cobrado", "Saldo_Pendiente", "Estado", "Fecha_Emision", "Fecha_Vencimiento"])
        
        for page in pages:
            props = page.get("properties", {})
            writer.writerow([
                page["id"],
                extract_property(props, "Proyecto"),
                extract_property(props, "Cliente"),
                extract_property(props, "Monto Total", 0),
                extract_property(props, "Monto Cobrado", 0),
                extract_property(props, "Saldo Pendiente", 0),
                extract_property(props, "Estado"),
                extract_property(props, "Fecha Emisión"),
                extract_property(props, "Fecha Vencimiento")
            ])
    
    print(f"   Exportados: {len(pages)} CxC")
    return len(pages)

def export_clientes():
    """Exporta Clientes a CSV"""
    print("Exportando Clientes...")
    pages = get_all_pages(CLIENTES_DB_ID)
    
    filename = os.path.join(OUTPUT_DIR, "clientes.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nombre", "Email", "Telefono"])
        
        for page in pages:
            props = page.get("properties", {})
            writer.writerow([
                page["id"],
                extract_property(props, "Nombre"),
                extract_property(props, "Email"),
                extract_property(props, "Teléfono")
            ])
    
    print(f"   Exportados: {len(pages)} clientes")
    return len(pages)

def main():
    print("=" * 60)
    print("EXPORTACION DE NOTION A CSV")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Crear directorio de exports
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Exportar cada tabla
    proyectos = export_proyectos()
    cxc = export_cxc()
    clientes = export_clientes()
    
    print()
    print("=" * 60)
    print("EXPORTACION COMPLETADA")
    print("=" * 60)
    print()
    print(f"Archivos creados en carpeta '{OUTPUT_DIR}':")
    print("   - proyectos.csv")
    print("   - cxc.csv")
    print("   - clientes.csv")
    print()
    print("Proximo paso: Importar estos CSVs en Google Sheets")

if __name__ == "__main__":
    main()
