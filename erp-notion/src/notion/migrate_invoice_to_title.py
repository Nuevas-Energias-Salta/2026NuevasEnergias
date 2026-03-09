import requests
import time

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
CXP_DB = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

print("Obteniendo todas las CxP...")

# Obtener todas las páginas
all_pages = []
has_more = True
start_cursor = None

while has_more:
    body = {}
    if start_cursor:
        body["start_cursor"] = start_cursor
    
    r = requests.post(f"https://api.notion.com/v1/databases/{CXP_DB}/query", 
                      headers=HEADERS, json=body)
    data = r.json()
    all_pages.extend(data.get("results", []))
    has_more = data.get("has_more", False)
    start_cursor = data.get("next_cursor")

print(f"Encontradas {len(all_pages)} páginas de CxP")

# Migrar cada página
migrated = 0
skipped = 0

for page in all_pages:
    page_id = page["id"]
    props = page.get("properties", {})
    
    # Obtener número de factura del campo "Numero factura" (rich_text)
    numero_factura_prop = props.get("Numero factura", {})
    numero_factura_content = numero_factura_prop.get("rich_text", [])
    
    if numero_factura_content:
        numero_factura = numero_factura_content[0].get("plain_text", "")
    else:
        numero_factura = ""
    
    # Obtener título actual
    titulo_prop = props.get("Descripcion1", {})
    titulo_content = titulo_prop.get("title", [])
    titulo_actual = titulo_content[0].get("plain_text", "") if titulo_content else ""
    
    if not numero_factura:
        print(f"  - Saltando {page_id}: sin número de factura")
        skipped += 1
        continue
    
    if titulo_actual == numero_factura:
        print(f"  - Saltando {page_id}: ya tiene el número correcto")
        skipped += 1
        continue
    
    # Actualizar el título con el número de factura
    update_body = {
        "properties": {
            "Descripcion1": {
                "title": [
                    {
                        "text": {
                            "content": numero_factura
                        }
                    }
                ]
            }
        }
    }
    
    r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", 
                       headers=HEADERS, json=update_body)
    
    if r.status_code == 200:
        print(f"  OK Migrado: '{titulo_actual}' -> '{numero_factura}'")
        migrated += 1
    else:
        print(f"  ERROR en {page_id}: {r.status_code}")
    
    # Pequeña pausa para no exceder rate limits
    time.sleep(0.3)

print(f"\n=== RESUMEN ===")
print(f"Migradas: {migrated}")
print(f"Saltadas: {skipped}")
print(f"Total: {len(all_pages)}")

