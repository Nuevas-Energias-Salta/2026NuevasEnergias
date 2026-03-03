import requests
import json

TOKEN = "YOUR_NOTION_TOKEN_HERE"
config.get_notion_headers()",
    "Notion-Version": "2022-06-28"
}

databases = {
    "CxC": "2e0c81c35804815a8755f4f254257f6a",
    "CxP": "2e0c81c358048123b1aed9b3579e0410",
    "Registro_Cobros": "2e0c81c35804810c89e0f99c6ed11ea5",
    "Registro_Pagos": "2e0c81c3580481b1bff1f1ced39bf4ac"
}

for name, db_id in databases.items():
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"Database ID: {db_id}")
    print("="*60)
    
    url = f"https://api.notion.com/v1/databases/{db_id}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        props = data.get("properties", {})
        
        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type", "unknown")
            extra = ""
            
            if prop_type == "relation":
                rel_db = prop_data.get("relation", {}).get("database_id", "")
                extra = f" -> {rel_db[:8]}..."
            elif prop_type == "rollup":
                rollup = prop_data.get("rollup", {})
                func = rollup.get("function", "")
                extra = f" ({func})"
            elif prop_type == "select":
                options = prop_data.get("select", {}).get("options", [])
                opt_names = [o.get("name", "") for o in options[:5]]
                extra = f" [{', '.join(opt_names)}]"
            elif prop_type == "formula":
                extra = " (calculated)"
            
            print(f"  - {prop_name}: {prop_type}{extra}")
    else:
        print(f"  Error: {response.status_code}")

