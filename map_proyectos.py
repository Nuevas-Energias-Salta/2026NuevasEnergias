import requests
import json

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Proyectos / Obras
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"

def get_proyectos_map():
    url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
    res = requests.post(url, headers=HEADERS, json={}).json()
    
    print("--- MAPA DE PROYECTOS (ID -> NOMBRE) ---")
    for item in res.get("results", []):
        p_id = item["id"]
        props = item.get("properties", {})
        title_list = props.get("Nombre", {}).get("title", [])
        name = title_list[0].get("plain_text", "N/A") if title_list else "N/A"
        print(f"ID: {p_id} -> Name: {name}")

get_proyectos_map()

