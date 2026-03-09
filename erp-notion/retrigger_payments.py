import requests
import json
from datetime import datetime, timedelta

# Configuración (Copiada del workflow de n8n)
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
PAGOS_DB_ID = "2e0c81c3-5804-81b1-bff1-f1ced39bf4ac"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def retrigger_recent_payments():
    print("Buscando pagos recientes para recalcular...")
    
    # Filtrar pagos de los últimos 3 días (ajustar si es necesario)
    three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
    
    payload = {
        "filter": {
            "timestamp": "last_edited_time",
            "last_edited_time": {
                "on_or_after": three_days_ago
            }
        }
    }
    
    url_query = f"https://api.notion.com/v1/databases/{PAGOS_DB_ID}/query"
    res = requests.post(url_query, headers=headers, json=payload)
    
    if res.status_code != 200:
        print(f"Error consultando Notion: {res.status_code} - {res.text}")
        return

    pages = res.json().get("results", [])
    print(f"Se encontraron {len(pages)} pagos recientes.")

    for i, page in enumerate(pages):
        page_id = page["id"]
        props = page["properties"]
        concepto = props.get("Concepto", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin concepto")
        
        print(f"[{i+1}/{len(pages)}] Re-disparando pago: {concepto} ({page_id})")
        
        # Realizar un "touch" (actualizar una propiedad con su mismo valor o algo inocuo)
        # Vamos a actualizar el 'Concepto' añadiendo un espacio invisible o simplemente el mismo valor
        # para forzar el evento 'pagedUpdatedInDatabase' en n8n.
        
        update_payload = {
            "properties": {
                "Concepto": {
                    "title": [{"text": {"content": concepto}}]
                }
            }
        }
        
        url_update = f"https://api.notion.com/v1/pages/{page_id}"
        res_upd = requests.patch(url_update, headers=headers, json=update_payload)
        
        if res_upd.status_code == 200:
            print("   ✅ Trigger enviado.")
        else:
            print(f"   ❌ Error: {res_upd.status_code}")

if __name__ == "__main__":
    retrigger_recent_payments()

