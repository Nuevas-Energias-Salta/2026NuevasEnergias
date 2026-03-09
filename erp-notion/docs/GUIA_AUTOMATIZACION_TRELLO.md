# 🔄 AUTOMATIZACIÓN TRELLO → NOTION (n8n)

## 🎯 Objetivo

Sincronizar automáticamente tarjetas nuevas/modificadas de Trello al sistema de gestión en Notion.

---

## 📋 ESTRATEGIA

**Opción A: Webhook de Trello** (Tiempo Real) ⭐ RECOMENDADA
- Trello notifica a n8n cuando hay cambios
- Respuesta inmediata (segundos)
- Requiere configurar webhook en Trello

**Opción B: Polling (Cada X minutos)**
- n8n revisa Trello cada X minutos
- Más simple de configurar
- Demora hasta X minutos

---

## 🚀 OPCIÓN A: WEBHOOK DE TRELLO (Recomendada)

### Paso 1: Crear Workflow en n8n

**Nodos:**

1. **Webhook** (escucha notificaciones de Trello)
2. **Filter** (solo tarjetas nuevas o modificadas)
3. **Get Custom Fields** (obtener email, celular, monto)
4. **Find/Create Cliente** (buscar o crear cliente)
5. **Create Proyecto** (crear en Notion)
6. **Create CxC** (auto-generar cuenta por cobrar)

---

### Paso 2: Configurar Webhook en Trello

Ejecutar este comando (o script):

```bash
curl -X POST "https://api.trello.com/1/tokens/TRELLO_TOKEN/webhooks/" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Sync to Notion",
    "callbackURL": "https://n8n.odontia.tech/webhook/trello-sync",
    "idModel": "612f6ea39c967b8bef5c2186"
  }' \
  -G \
  -d "key=TRELLO_API_KEY"
```

Reemplazar:
- `TRELLO_TOKEN`: Tu token
- `TRELLO_API_KEY`: Tu API key
- `callbackURL`: URL del webhook de n8n

---

## 🔧 OPCIÓN B: POLLING (Más Simple)

### Workflow en n8n:

1. **Schedule Trigger** (cada 15 min)
2. **HTTP Request** → Trello API (obtener tarjetas de últimos 15 min)
3. **Check Existing** (verificar si ya existe en Notion)
4. **Process New Cards** (crear proyecto + CxC)

---

## 💾 SCRIPTS DE APOYO

### Script para registrar webhook de Trello:

Archivo: `setup_trello_webhook.py`

```python
import requests

TRELLO_API_KEY = "f529e10ec3bac9427b5c1abcfa2ec821"
TRELLO_TOKEN = "ATTA4a2d8d0148cae05d395044b7779d80db44ae465d82aecdb32b0067daf008eeea7221D17C"
BOARD_ID = "612f6ea39c967b8bef5c2186"
WEBHOOK_URL = "https://n8n.odontia.tech/webhook/trello-sync"

url = f"https://api.trello.com/1/webhooks"
params = {
    'key': TRELLO_API_KEY,
    'token': TRELLO_TOKEN
}
data = {
    'description': 'Sync to Notion ERP',
    'callbackURL': WEBHOOK_URL,
    'idModel': BOARD_ID
}

response = requests.post(url, params=params, json=data)
print(response.json())
```

---

## 📊 WORKFLOW N8N COMPLETO

Te voy a crear el JSON del workflow que importás en n8n.

¿Preferís empezar con:
- **Opción A** (webhook - tiempo real)?
- **Opción B** (polling - cada 15 min)?

---

**Decime cuál opción preferís y te armo el workflow completo listo para importar** 🚀
