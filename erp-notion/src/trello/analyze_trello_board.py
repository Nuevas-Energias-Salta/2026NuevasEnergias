"""
Script para analizar un tablero específico de Trello ("Kanban Nuevas Energías").
Objetivo: Entender la estructura (Listas, Cards, Etiquetas, Custom Fields) para diseñar la BD en Notion.
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

# Credenciales Trello
config.TRELLO_API_KEY
config.TRELLO_TOKEN
BOARD_ID = "612f6ea39c967b8bef5c2186" # Kanban Nuevas Energías

def analyze_board():
    # 1. Obtener Listas (Estados del Kanban)
    lists_url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
    query = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}
    
    print(f"📊 Analizando tablero: Kanban Nuevas Energías ({BOARD_ID})")
    print("=" * 60)
    
    try:
        lists = requests.get(lists_url, params=query).json()
        print("\n📝 LISTAS (Posibles Estados en Notion):")
        for lst in lists:
            print(f"   - {lst['name']}")
            
        # 2. Obtener Custom Fields (Campos personalizados)
        fields_url = f"https://api.trello.com/1/boards/{BOARD_ID}/customFields"
        fields = requests.get(fields_url, params=query).json()
        
        print("\n🔧 CUSTOM FIELDS (Campos a crear en Notion):")
        if fields:
            for field in fields:
                options = ""
                if field.get('options'):
                    opts = [opt['value']['text'] for opt in field['options']]
                    options = f" (Opciones: {', '.join(opts)})"
                print(f"   - {field['name']} ({field['type']}){options}")
        else:
            print("   (No se encontraron Custom Fields)")

        # 3. Obtener una muestra de tarjetas para ver datos reales
        cards_url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
        cards_query = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN, 'limit': 5} # Solo 5 para no saturar
        cards = requests.get(cards_url, params=cards_query).json()
        
        print("\n🃏 MUESTRA DE TARJETAS (Ejemplos):")
        for card in cards:
            print(f"   - {card['name']}")
            if card['desc']:
                 print(f"     Desc (inicio): {card['desc'][:50]}...")
            if card['labels']:
                labels = [l['name'] for l in card['labels']]
                print(f"     Etiquetas: {', '.join(labels)}")
            print("-" * 30)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error analizando el tablero: {e}")

if __name__ == "__main__":
    analyze_board()
