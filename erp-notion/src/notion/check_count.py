import sys
import os
import requests
import json
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

config.NOTION_TOKEN
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"
config.get_notion_headers()", "Notion-Version": "2022-06-28"}
url = f"https://api.notion.com/v1/databases/{PROYECTOS_DB_ID}/query"
res = requests.post(url, headers=HEADERS, json={})
print(f"Registros restantes: {len(res.json().get('results', []))}")
