import requests

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28"
}

ASIGNACIONES_DB_ID = "2eec81c3-5804-8198-837b-c13a979dd872"

r = requests.get(f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}", headers=HEADERS)
props = r.json().get("properties", {})

print("=== Propiedades en Asignaciones de Pagos ===")
for name, data in props.items():
    prop_type = data.get("type")
    if prop_type == "relation":
        rel = data.get("relation", {})
        print(f"  - {name}: relation -> {rel.get('database_id')} (type: {rel.get('type')})")
        # Check if it has dual_property info
        if rel.get("type") == "dual_property":
            print(f"      Synced property ID: {rel.get('dual_property', {}).get('synced_property_id')}")
    else:
        print(f"  - {name}: {prop_type}")

