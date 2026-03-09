"""
Script para verificar webhooks activos en Trello
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


config.TRELLO_API_KEY
config.TRELLO_TOKEN

print("Verificando webhooks activos en Trello...\n")

url = "https://api.trello.com/1/tokens/" + TRELLO_TOKEN + "/webhooks"
params = {
    'key': TRELLO_API_KEY
}

try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        webhooks = response.json()
        
        if len(webhooks) == 0:
            print("No hay webhooks registrados")
        else:
            print(f"Total de webhooks activos: {len(webhooks)}\n")
            
            for wh in webhooks:
                print(f"ID: {wh['id']}")
                print(f"Descripcion: {wh.get('description', 'N/A')}")
                print(f"URL: {wh['callbackURL']}")
                print(f"Activo: {'Si' if wh['active'] else 'No'}")
                print("-" * 60)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")
