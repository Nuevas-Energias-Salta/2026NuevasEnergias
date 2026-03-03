import requests

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28"
}

CXP_DB_ID = "2e0c81c358048123b1aed9b3579e0410"

r = requests.get(f"https://api.notion.com/v1/databases/{CXP_DB_ID}", headers=HEADERS)
props = r.json().get("properties", {})

print("=== Relaciones en CxP ===")
for name, data in props.items():
    if data.get("type") == "relation":
        rel_db = data.get("relation", {}).get("database_id", "")
        sync_type = data.get("relation", {}).get("type", "")
        print(f"  - {name}: -> {rel_db} ({sync_type})")

