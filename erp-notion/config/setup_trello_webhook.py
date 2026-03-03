"""
Script para registrar webhook de Trello -> n8n
Esto hace que Trello notifique a n8n INSTANTÁNEAMENTE cuando hay cambios
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

TRELLO_API_KEY = "f529e10ec3bac9427b5c1abcfa2ec821"
TRELLO_TOKEN = "ATTA4a2d8d0148cae05d395044b7779d80db44ae465d82aecdb32b0067daf008eeea7221D17C"
BOARD_ID = "612f6ea39c967b8bef5c2186"
WEBHOOK_URL = "https://n8n.odontia.tech/webhook/trello-sync"

print("Registrando webhook de Trello...")
print(f"Board ID: {BOARD_ID}")
print(f"Webhook URL: {WEBHOOK_URL}")

url = "https://api.trello.com/1/webhooks"
params = {
    'key': TRELLO_API_KEY,
    'token': TRELLO_TOKEN
}
data = {
    'description': 'Sync to Notion ERP - Tiempo Real',
    'callbackURL': WEBHOOK_URL,
    'idModel': BOARD_ID
}

try:
    response = requests.post(url, params=params, json=data)
    if response.status_code == 200:
        result = response.json()
        print("\nWebhook registrado exitosamente!")
        print(f"ID del webhook: {result['id']}")
        print("\nAhora Trello notificara a n8n INSTANTANEAMENTE cuando:")
        print("  - Se cree una tarjeta nueva")
        print("  - Se modifique una tarjeta existente")
        print("  - Se mueva una tarjeta de lista")
    else:
        print(f"\nError: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\nError: {str(e)}")
