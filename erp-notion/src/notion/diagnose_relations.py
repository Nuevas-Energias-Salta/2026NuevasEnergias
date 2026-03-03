import requests

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()", "Notion-Version": "2022-06-28"}

print("="*60)
print("DIAGNOSTICO DE RELACIONES")
print("="*60)

# Registro de Pagos
print("\n1. REGISTRO DE PAGOS")
r = requests.get("https://api.notion.com/v1/databases/2e0c81c3580481b1bff1f1ced39bf4ac", headers=HEADERS)
props = r.json().get("properties", {})
for name, data in props.items():
    if data.get("type") == "relation":
        rel = data.get("relation", {})
        print(f"   - '{name}': -> {rel.get('database_id')[:20]}... (type: {rel.get('type')})")

# CxP
print("\n2. CUENTAS POR PAGAR")
r = requests.get("https://api.notion.com/v1/databases/2e0c81c358048123b1aed9b3579e0410", headers=HEADERS)
props = r.json().get("properties", {})
for name, data in props.items():
    if data.get("type") in ["relation", "rollup"]:
        if data.get("type") == "relation":
            rel = data.get("relation", {})
            print(f"   - '{name}': RELATION -> {rel.get('database_id')[:20]}... (type: {rel.get('type')})")
        else:
            rollup = data.get("rollup", {})
            print(f"   - '{name}': ROLLUP (relation: {rollup.get('relation_property_id')}, func: {rollup.get('function')})")

# Asignaciones de Pagos
print("\n3. ASIGNACIONES DE PAGOS")
r = requests.get("https://api.notion.com/v1/databases/2eec81c3-5804-8198-837b-c13a979dd872", headers=HEADERS)
props = r.json().get("properties", {})
for name, data in props.items():
    ptype = data.get("type")
    if ptype == "relation":
        rel = data.get("relation", {})
        print(f"   - '{name}': -> {rel.get('database_id')[:20]}... (type: {rel.get('type')})")
    else:
        print(f"   - '{name}': {ptype}")

