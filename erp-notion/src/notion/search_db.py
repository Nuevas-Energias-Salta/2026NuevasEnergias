import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Buscar la base de datos
response = requests.post(
    "https://api.notion.com/v1/search",
    headers=HEADERS,
    json={
        "query": "Asignaciones de Pagos",
        "filter": {"property": "object", "value": "database"}
    }
)

data = response.json()
results = data.get("results", [])

print(f"Found {len(results)} results")
for db in results:
    title_arr = db.get("title", [])
    title = title_arr[0].get("plain_text", "") if title_arr else "No title"
    db_id = db.get("id", "")
    print(f"- {title}: {db_id}")

