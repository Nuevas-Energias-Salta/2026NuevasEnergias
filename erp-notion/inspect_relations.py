import requests
import json

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

def inspect_db_relations(db_id, name):
    print(f"\n--- Investigando {name} ---")
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    res = requests.post(url, headers=HEADERS, json={"page_size": 5}).json()
    
    for item in res.get("results", []):
        props = item.get("properties", {})
        print(f"\nItem: {item.get('id')}")
        for prop_name, prop_val in props.items():
            if prop_val.get("type") == "relation":
                print(f"  Propiedad: {prop_name} (relation)")
                print(f"  Contenido: {json.dumps(prop_val.get('relation', []), indent=2)}")

inspect_db_relations(CXC_DB_ID, "Cuentas por Cobrar")
inspect_db_relations(CXP_DB_ID, "Cuentas por Pagar")

