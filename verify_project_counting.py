import requests
import json

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 1. Get active cost centers
print("Fetching active cost centers...")
res_cc = requests.post(f"https://api.notion.com/v1/databases/{CENTROS_DB_ID}/query", headers=headers, json={
    "filter": {"property": "Activo", "checkbox": {"equals": True}}
})
active_cc_ids = [cc["id"] for cc in res_cc.json().get("results", [])]
print(f"Active CC count: {len(active_cc_ids)}")

# 2. Get all projects
print("Fetching all projects...")
res_proj = requests.post(f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query", headers=headers)
projects = res_proj.json().get("results", [])

linked_projects = 0
for p in projects:
    cc_rel = p["properties"].get("Centro de Costo", {}).get("relation", [])
    if cc_rel and cc_rel[0]["id"] in active_cc_ids:
        linked_projects += 1

print(f"Projects linked to active CCs: {linked_projects}")
print(f"Total projects: {len(projects)}")

