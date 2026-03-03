"""
Script rápido para obtener ID de Resumen CxC
"""

import sys
import os
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


config.NOTION_TOKEN

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = "https://api.notion.com/v1/search"
payload = {
    "query": "Resumen CxC",
    "filter": {"property": "object", "value": "database"}
}

res = requests.post(url, headers=HEADERS, json=payload)
results = res.json().get("results", [])

for result in results:
    title = result.get("title", [{}])[0].get("text", {}).get("content", "")
    if "Resumen CxC" in title:
        print("ID de Resumen CxC:")
        print(result["id"])
        break

