import requests
import json
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def list_all_databases():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    print("🔍 Buscando TODAS las bases de datos disponibles...")
    
    try:
        search_url = f"{NOTION_BASE_URL}/search"
        search_payload = {
            "filter": {
                "property": "object",
                "value": "database"
            }
        }
        
        response = requests.post(search_url, headers=headers, json=search_payload)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✅ Se encontraron {len(results)} bases de datos:\n")
            
            for db in results:
                title_list = db.get("title", [])
                if title_list:
                    title = title_list[0].get("text", {}).get("content", "Sin Título")
                else:
                    title = "Sin Título"
                
                print(f"📌 Nombre: {title}")
                print(f"   ID: {db['id']}")
                print("-" * 40)
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    list_all_databases()

