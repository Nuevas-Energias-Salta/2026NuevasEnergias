import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

ASIGNACIONES_DB_ID = "2eec81c3-5804-8198-837b-c13a979dd872"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

# Obtener el ID de la propiedad CxP en Asignaciones
r = requests.get(f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}", headers=HEADERS)
asig_props = r.json().get("properties", {})

cxp_prop_id = None
for name, data in asig_props.items():
    if name == "CxP":
        cxp_prop_id = data.get("id")
        print(f"CxP property ID in Asignaciones: {cxp_prop_id}")

# Actualizar la relacion CxP en Asignaciones para que sea bidireccional
# La API no permite modificar el tipo de relacion una vez creada
# En su lugar, debemos eliminar la relacion existente y crear una nueva con dual_property

# Primero eliminar la propiedad Asignaciones de CxP
print("\nEliminando propiedad 'Asignaciones' de CxP...")
delete_payload = {
    "properties": {
        "Asignaciones": None
    }
}
r = requests.patch(f"https://api.notion.com/v1/databases/{CXP_DB_ID}", headers=HEADERS, json=delete_payload)
print(f"Delete result: {r.status_code}")

# Ahora actualizar la relacion CxP en Asignaciones para que cree una propiedad sincronizada en CxP
print("\nActualizando relacion CxP en Asignaciones para que sea bidireccional...")
update_payload = {
    "properties": {
        "CxP": {
            "relation": {
                "database_id": CXP_DB_ID,
                "type": "dual_property",
                "dual_property": {}
            }
        }
    }
}
r = requests.patch(f"https://api.notion.com/v1/databases/{ASIGNACIONES_DB_ID}", headers=HEADERS, json=update_payload)
print(f"Update result: {r.status_code}")
if r.status_code != 200:
    print(r.text)
else:
    print("Relacion actualizada exitosamente!")
    
    # Verificar que se creo la propiedad sincronizada en CxP
    r = requests.get(f"https://api.notion.com/v1/databases/{CXP_DB_ID}", headers=HEADERS)
    cxp_props = r.json().get("properties", {})
    print("\nNuevas relaciones en CxP:")
    for name, data in cxp_props.items():
        if data.get("type") == "relation":
            rel = data.get("relation", {})
            if "asig" in name.lower() or "cxp" in name.lower():
                print(f"  - {name}: -> {rel.get('database_id')[:20]}... (type: {rel.get('type')})")

