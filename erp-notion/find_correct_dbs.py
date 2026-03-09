#!/usr/bin/env python3
"""
Diagnóstico de bases de datos financieras - sin emojis
"""

import requests
import json

NOTION_TOKEN = 'YOUR_NOTION_TOKEN_HERE'
NOTION_VERSION = '2022-06-28'
NOTION_BASE_URL = 'https://api.notion.com/v1'

headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': NOTION_VERSION
}

print('=== BUSCANDO BASES DE DATOS FINANCIERAS ===')

# Buscar todas las bases de datos
search_url = f'{NOTION_BASE_URL}/search'
search_payload = {
    'filter': {
        'property': 'object',
        'value': 'database'
    }
}

response = requests.post(search_url, headers=headers, json=search_payload)
if response.status_code == 200:
    databases = response.json().get('results', [])
    print(f'Total de bases encontradas: {len(databases)}')
    
    financial_dbs = []
    for db in databases:
        title = db.get('title', [{}])[0].get('text', {}).get('content', 'Sin título')
        db_id = db.get('id', '')
        
        # Buscar bases que puedan ser financieras
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in ['cuentas', 'cxc', 'cxp', 'cobrar', 'pagar', 'factura', 'pago', 'ingreso', 'egreso']):
            financial_dbs.append({'title': title, 'id': db_id})
            print(f'   [FINANCIERA] {title} (ID: {db_id[:8]}...)')
        elif any(keyword in title_lower for keyword in ['cliente', 'proveedor', 'centro', 'proyecto']):
            print(f'   [CONTACTO]   {title} (ID: {db_id[:8]}...)')
        else:
            print(f'   [OTRA]       {title} (ID: {db_id[:8]}...)')
    
    print(f'\nBases financieras encontradas: {len(financial_dbs)}')
    
    # Guardar IDs correctos
    correct_ids = {}
    
    # Si encontramos bases financieras, verificar su estructura
    for db in financial_dbs:
        print(f'\n--- Verificando: {db["title"]} ---')
        try:
            query_url = f'{NOTION_BASE_URL}/databases/{db["id"]}/query'
            query_response = requests.post(query_url, headers=headers, json={'page_size': 3})
            
            if query_response.status_code == 200:
                results = query_response.json().get('results', [])
                if results:
                    sample = results[0]
                    props = sample.get('properties', {})
                    
                    # Buscar campos relevantes
                    amount_fields = [k for k in props.keys() if any(keyword in k.lower() for keyword in ['monto', 'amount', 'importe', 'total'])]
                    status_fields = [k for k in props.keys() if any(keyword in k.lower() for keyword in ['estado', 'status', 'pagada'])]
                    
                    print(f'   Registros: {len(results)}')
                    print(f'   Campos de monto: {amount_fields}')
                    print(f'   Campos de estado: {status_fields}')
                    
                    # Guardar ID correcto
                    if 'cuentas por cobrar' in db['title'].lower():
                        correct_ids['CXC'] = db['id']
                        print(f'   [GUARDADO] ID correcto para CxC: {db["id"]}')
                    elif 'cuentas por pagar' in db['title'].lower():
                        correct_ids['CXP'] = db['id']
                        print(f'   [GUARDADO] ID correcto para CxP: {db["id"]}')
                    
                    # Mostrar un ejemplo
                    if amount_fields:
                        field = amount_fields[0]
                        value = props[field].get('number', 0)
                        print(f'   Ejemplo {field}: {value}')
        except Exception as e:
            print(f'   Error verificando: {e}')
    
    # Guardar configuración correcta
    if correct_ids:
        print(f'\n=== CONFIGURACIÓN CORRECTA ENCONTRADA ===')
        config_content = f'''#!/usr/bin/env python3
"""
Configuración corregida de IDs de bases de datos financieras
"""

# IDs CORRECTOS de bases de datos financieras
NOTION_CXC_DB_ID = "{correct_ids.get('CXC', 'NO_ENCONTRADO')}"
NOTION_CXP_DB_ID = "{correct_ids.get('CXP', 'NO_ENCONTRADO')}"
NOTION_CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"  # Este sí es correcto

print("IDs corregidos:")
print(f"CxC: {NOTION_CXC_DB_ID}")
print(f"CxP: {NOTION_CXP_DB_ID}")
print(f"Centros: {NOTION_CENTROS_DB_ID}")
'''
        
        with open('correct_ids_config.py', 'w') as f:
            f.write(config_content)
        
        print(f'Configuración guardada en: correct_ids_config.py')
    else:
        print('\n[ERROR] No se encontraron bases de datos financieras válidas')
else:
    print(f'Error buscando bases: {response.status_code}')
