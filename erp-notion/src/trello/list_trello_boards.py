"""
Script para conectar con Trello y listar los tableros disponibles.
Paso 1 del análisis: Identificar el tablero correcto.
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

def list_boards():
    url = "https://api.trello.com/1/members/me/boards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'fields': 'name,id,url'  # Solo traemos lo necesario
    }

    try:
        response = requests.get(url, params=query)
        response.raise_for_status()
        boards = response.json()
        
        print(f"✅ Conexión exitosa con Trello. Se encontraron {len(boards)} tableros:")
        print("-" * 50)
        for board in boards:
            print(f"📋 Nombre: {board['name']}")
            print(f"🆔 ID: {board['id']}")
            print("-" * 50)
            
        return boards

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando a Trello: {e}")
        return None

if __name__ == "__main__":
    list_boards()
