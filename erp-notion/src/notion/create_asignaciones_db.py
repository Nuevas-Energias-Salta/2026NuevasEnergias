import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# IDs de las bases de datos existentes
CXP_DB_ID = "2e0c81c358048123b1aed9b3579e0410"
REGISTRO_PAGOS_DB_ID = "2e0c81c3580481b1bff1f1ced39bf4ac"

# Primero obtener el parent de CxP para crear la nueva DB en el mismo lugar
response = requests.get(
    f"https://api.notion.com/v1/databases/{CXP_DB_ID}",
    headers=HEADERS
)

if response.status_code != 200:
    print(f"Error getting CxP info: {response.text}")
    exit(1)

cxp_info = response.json()
parent = cxp_info.get("parent", {})
print(f"Parent type: {parent.get('type')}")
print(f"Parent ID: {parent.get('page_id') or parent.get('workspace')}")

parent_page_id = parent.get("page_id")

if not parent_page_id:
    print("Could not find parent page ID")
    exit(1)

# Crear la nueva base de datos "Asignaciones de Pagos"
new_db_payload = {
    "parent": {
        "type": "page_id",
        "page_id": parent_page_id
    },
    "title": [
        {
            "type": "text",
            "text": {
                "content": "Asignaciones de Pagos"
            }
        }
    ],
    "properties": {
        "Concepto": {
            "title": {}
        },
        "Monto Asignado": {
            "number": {
                "format": "dollar"
            }
        },
        "CxP": {
            "relation": {
                "database_id": CXP_DB_ID,
                "single_property": {}
            }
        },
        "Pago": {
            "relation": {
                "database_id": REGISTRO_PAGOS_DB_ID,
                "single_property": {}
            }
        },
        "Fecha": {
            "date": {}
        }
    }
}

print("\nCreating 'Asignaciones de Pagos' database...")
response = requests.post(
    "https://api.notion.com/v1/databases",
    headers=HEADERS,
    json=new_db_payload
)

if response.status_code == 200:
    result = response.json()
    new_db_id = result.get("id")
    print(f"✅ Database created successfully!")
    print(f"Database ID: {new_db_id}")
    print(f"\nSave this ID for the n8n workflow!")
else:
    print(f"❌ Error creating database: {response.status_code}")
    print(response.text)

