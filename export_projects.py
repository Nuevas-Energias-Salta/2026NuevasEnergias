import requests
import json
import sys
import io
import csv

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

CENTROS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f" # Proyectos/Obras

def get_text_property(props, name):
    """Extrae texto plano de una propiedad rich_text o title"""
    if name not in props: return ""
    prop = props[name]
    if prop['type'] == 'title' and prop['title']:
        return prop['title'][0]['plain_text']
    elif prop['type'] == 'rich_text' and prop['rich_text']:
        return prop['rich_text'][0]['plain_text']
    return ""

def export_projects():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    filename = "verificacion_proyectos.csv"
    print(f"📄 Generando reporte de PROYECTOS en: {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        # Intentaremos capturar algunas columnas comunes además del nombre
        writer.writerow(['NOMBRE PROYECTO', 'ESTADO/STATUS', 'ID NOTION'])
        
        has_more = True
        next_cursor = None
        count = 0
        
        while has_more:
            payload = {"page_size": 100}
            if next_cursor: payload["start_cursor"] = next_cursor
            
            res = requests.post(f"{NOTION_BASE_URL}/databases/{CENTROS_DB_ID}/query", headers=headers, json=payload)
            if res.status_code != 200:
                print(f"❌ Error Proyectos: {res.text}")
                break
                
            data = res.json()
            for item in data.get("results", []):
                props = item['properties']
                
                # Buscar Nombre (Title)
                nombre = ""
                # Estrategia: Buscar la propiedad que sea type="title"
                for k, v in props.items():
                    if v['type'] == 'title':
                        nombre = get_text_property(props, k)
                        break
                
                # Buscar Estado
                estado = ""
                # Estrategia: Buscar propiedad select que se llame parecida a Estado
                for k, v in props.items():
                    if v['type'] == 'select' and v['select']:
                        if any(x in k.lower() for x in ['estado', 'status']):
                            estado = v['select']['name']
                            break
                
                writer.writerow([nombre, estado, item['id']])
                count += 1
            
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

    print(f"\n✅ Reporte de Proyectos generado exitosamente.")
    print(f"   - {count} Proyectos exportados")
    print(f"   👉 Abre el archivo '{filename}' en Excel.")

if __name__ == "__main__":
    export_projects()

