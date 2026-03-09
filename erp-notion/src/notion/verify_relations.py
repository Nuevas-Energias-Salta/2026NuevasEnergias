import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

ASIGNACIONES_DB_ID = "2eec81c3-5804-8198-837b-c13a979dd872"
CXP_DB_ID = "2e0c81c358048123b1aed9b3579e0410"

# Verificar estructura de Asignaciones de Pagos
print("=== Asignaciones de Pagos ===")
response = requests.get(
    f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}",
    headers=HEADERS
)
if response.status_code == 200:
    props = response.json().get("properties", {})
    for name, data in props.items():
        prop_type = data.get("type")
        print(f"  - {name}: {prop_type}")
        if prop_type == "relation":
            print(f"      -> {data.get('relation', {}).get('database_id', '')[:20]}...")
else:
    print(f"Error: {response.status_code}")

# Verificar que CxP tenga la relacion inversa
print("\n=== CxP (verificar relacion a Asignaciones) ===")
response = requests.get(
    f"https://api.notion.com/v1/databases/{CXP_DB_ID}",
    headers=HEADERS
)
if response.status_code == 200:
    props = response.json().get("properties", {})
    for name, data in props.items():
        prop_type = data.get("type")
        if "asignac" in name.lower() or prop_type == "relation":
            print(f"  - {name}: {prop_type}")
            if prop_type == "relation":
                rel_id = data.get("relation", {}).get("database_id", "")
                print(f"      -> {rel_id[:20]}...")
else:
    print(f"Error: {response.status_code}")

