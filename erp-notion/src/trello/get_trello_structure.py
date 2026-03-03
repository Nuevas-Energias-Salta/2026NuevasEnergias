"""
Script para obtener la estructura completa del Board de Trello
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

import json

config.TRELLO_API_KEY
config.TRELLO_TOKEN
BOARD_ID = "612f6ea39c967b8bef5c2186"

def get_board_info():
    """Obtiene info del board"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}"
    params = config.get_trello_params()
    res = requests.get(url, params=params)
    return res.json()

def get_lists():
    """Obtiene todas las listas"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    params = config.get_trello_params()
    return requests.get(url, params=params).json()

def get_custom_fields():
    """Obtiene custom fields"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/customFields"
    params = config.get_trello_params()
    return requests.get(url, params=params).json()

def get_labels():
    """Obtiene etiquetas"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/labels"
    params = config.get_trello_params()
    return requests.get(url, params=params).json()

def get_sample_card():
    """Obtiene una tarjeta de ejemplo con todos sus campos"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    params = {
        'key': TRELLO_API_KEY, 
        'token': TRELLO_TOKEN,
        'limit': 1,
        'customFieldItems': 'true',
        'checklists': 'all'
    }
    cards = requests.get(url, params=params).json()
    if cards:
        return cards[0]
    return None

def main():
    print("=" * 70)
    print("ESTRUCTURA DEL BOARD DE TRELLO")
    print("=" * 70)
    
    # Info del board
    board = get_board_info()
    print(f"\nBoard: {board.get('name', 'N/A')}")
    print(f"URL: {board.get('url', 'N/A')}")
    
    # Listas
    print("\n" + "-" * 40)
    print("LISTAS:")
    print("-" * 40)
    lists = get_lists()
    for i, lst in enumerate(lists, 1):
        print(f"   {i}. {lst['name']}")
    
    # Custom Fields
    print("\n" + "-" * 40)
    print("CUSTOM FIELDS:")
    print("-" * 40)
    custom_fields = get_custom_fields()
    if custom_fields:
        for cf in custom_fields:
            cf_type = cf.get('type', 'unknown')
            options = ""
            if cf_type == 'list' and cf.get('options'):
                opts = [o['value']['text'] for o in cf['options']]
                options = f" [{', '.join(opts)}]"
            print(f"   - {cf['name']} ({cf_type}){options}")
    else:
        print("   (No hay custom fields)")
    
    # Labels
    print("\n" + "-" * 40)
    print("ETIQUETAS (Labels):")
    print("-" * 40)
    labels = get_labels()
    for label in labels:
        if label.get('name'):
            print(f"   - {label['name']} ({label.get('color', 'sin color')})")
    
    # Tarjeta de ejemplo
    print("\n" + "-" * 40)
    print("TARJETA DE EJEMPLO:")
    print("-" * 40)
    card = get_sample_card()
    if card:
        print(f"   Nombre: {card.get('name', 'N/A')}")
        print(f"   Descripcion: {card.get('desc', 'N/A')[:100]}...")
        
        # Custom field values
        if card.get('customFieldItems'):
            print("\n   Custom Fields:")
            cf_dict = {cf['id']: cf['name'] for cf in custom_fields}
            for cfv in card['customFieldItems']:
                cf_name = cf_dict.get(cfv['idCustomField'], 'Unknown')
                value = cfv.get('value', {})
                val_str = str(value.get('text') or value.get('number') or value.get('checked') or 'N/A')
                print(f"      - {cf_name}: {val_str}")
        
        # Checklists
        if card.get('checklists'):
            print("\n   Checklists:")
            for cl in card['checklists']:
                print(f"      - {cl['name']}")
                for item in cl.get('checkItems', []):
                    estado = "[x]" if item['state'] == 'complete' else "[ ]"
                    print(f"         {estado} {item['name']}")
    
    print("\n" + "=" * 70)
    print("FIN DE ESTRUCTURA")
    print("=" * 70)

if __name__ == "__main__":
    main()
