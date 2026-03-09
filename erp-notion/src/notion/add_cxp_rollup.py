import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

CXP_DB_ID = "2e0c81c358048123b1aed9b3579e0410"
ASIGNACIONES_DB_ID = "2eec81c3-5804-8198-837b-c13a979dd872"

# Agregar propiedades a CxP:
# 1. Relacion a Asignaciones
# 2. Rollup que sume Monto Asignado desde Asignaciones

# Primero verificar el nombre exacto de la propiedad CxP en Asignaciones
response = requests.get(
    f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}",
    headers=HEADERS
)
asig_props = response.json().get("properties", {})
cxp_prop_id = None
for name, data in asig_props.items():
    if name == "CxP":
        cxp_prop_id = data.get("id")
        print(f"Found CxP property in Asignaciones: {name} (id: {cxp_prop_id})")

# Agregar la relacion y rollup a CxP
update_payload = {
    "properties": {
        "Asignaciones": {
            "relation": {
                "database_id": ASIGNACIONES_DB_ID,
                "single_property": {}
            }
        }
    }
}

print("\nAdding 'Asignaciones' relation to CxP...")
response = requests.patch(
    f"https://api.notion.com/v1/databases/{CXP_DB_ID}",
    headers=HEADERS,
    json=update_payload
)

if response.status_code == 200:
    print("Relation added successfully!")
    
    # Ahora agregar el rollup
    # Primero obtener el id de la propiedad Monto Asignado en Asignaciones
    asig_response = requests.get(
        f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}",
        headers=HEADERS
    )
    asig_data = asig_response.json()
    monto_prop_id = None
    for name, data in asig_data.get("properties", {}).items():
        if name == "Monto Asignado":
            monto_prop_id = data.get("id")
            print(f"Found Monto Asignado property: {monto_prop_id}")
    
    # Obtener el id de la propiedad Asignaciones que acabamos de crear
    cxp_response = requests.get(
        f"https://api.notion.com/v1/databases/{CXP_DB_ID}",
        headers=HEADERS
    )
    cxp_data = cxp_response.json()
    asig_rel_prop_id = None
    for name, data in cxp_data.get("properties", {}).items():
        if name == "Asignaciones":
            asig_rel_prop_id = data.get("id")
            print(f"Found Asignaciones relation property in CxP: {asig_rel_prop_id}")
    
    if asig_rel_prop_id and monto_prop_id:
        rollup_payload = {
            "properties": {
                "Monto Asignado Total": {
                    "rollup": {
                        "relation_property_id": asig_rel_prop_id,
                        "rollup_property_id": monto_prop_id,
                        "function": "sum"
                    }
                }
            }
        }
        
        print("\nAdding 'Monto Asignado Total' rollup to CxP...")
        response = requests.patch(
            f"https://api.notion.com/v1/databases/{CXP_DB_ID}",
            headers=HEADERS,
            json=rollup_payload
        )
        
        if response.status_code == 200:
            print("Rollup added successfully!")
        else:
            print(f"Error adding rollup: {response.status_code}")
            print(response.text)
else:
    print(f"Error adding relation: {response.status_code}")
    print(response.text)

