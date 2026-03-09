import requests
import time

NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_pages():
    url = f"https://api.notion.com/v1/databases/{CXP_DB_ID}/query"
    results = []
    has_more = True
    next_cursor = None
    
    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            results.extend(data["results"])
            has_more = data["has_more"]
            next_cursor = data.get("next_cursor")
        else:
            print(f"Error fetching pages: {res.status_code}")
            break
    return results

def sync_monto_pagado():
    pages = get_pages()
    print(f"Processing {len(pages)} pages...")
    
    updated_count = 0
    for page in pages:
        props = page["properties"]
        page_id = page["id"]
        
        # Get Rollup value (lupa)
        # We saw id 'Tbss' is "Monto Pagado " rollup and 'zoYE' is "Monto Asignado Total" rollup
        rollup_val = props.get("Monto Asignado Total", {}).get("rollup", {}).get("number", 0) or \
                     props.get("Monto Pagado ", {}).get("rollup", {}).get("number", 0) or 0
        
        # Get Number value (#)
        number_val = props.get("Monto pagado", {}).get("number", 0) or 0
        
        # If they differ, update Number value
        if abs(rollup_val - number_val) > 0.01:
            print(f"Updating '{page_id}': Rollup={rollup_val}, Number={number_val} -> Synchronization")
            update_payload = {
                "properties": {
                    "Monto pagado": {"number": rollup_val}
                }
            }
            # We also check if it should be Pagado if rollup >= monto
            monto_total = props.get("Monto", {}).get("number", 0) or 0
            if rollup_val >= (monto_total - 0.01) and props.get("Estado", {}).get("select", {}).get("name") != "Pagado":
                 update_payload["properties"]["Estado"] = {"select": {"name": "Pagado"}}
            
            res = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, json=update_payload)
            if res.status_code == 200:
                updated_count += 1
            else:
                print(f"Error updating {page_id}: {res.status_code} - {res.text}")
            
            # rate limit safety
            time.sleep(0.3)

    print(f"Finished. Updated {updated_count} pages.")

if __name__ == "__main__":
    sync_monto_pagado()

