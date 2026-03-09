# 🚀 IMPLEMENTACIÓN FINAL - Calculadora CxC Online

## ✅ Configuración de Producción

**n8n:** https://n8n.odontia.tech/  
**Webhook:** https://n8n.odontia.tech/webhook/calcular-cxc  
**Formulario:** Se hosteará en GitHub Pages

---

## 📋 PASO 1: Importar Workflow en n8n

### 1.1 Acceder a n8n

1. Ir a https://n8n.odontia.tech/
2. Iniciar sesión

### 1.2 Importar Workflow

1. Click en **"Workflows"** (menú lateral)
2. Click en **"+"** → **"Import from File"**
3. Seleccionar archivo: `workflow_n8n_production.json`
4. Click en **"Import"**

### 1.3 Configurar Credenciales de Notion

1. En el workflow importado, verás nodos de Notion marcados en rojo
2. Click en cualquier nodo de Notion
3. En "Credential to connect with" → Click **"Create New"**
4. Nombre: "Notion API - ERP"
5. API Key: `YOUR_NOTION_TOKEN_HERE`
6. Click **"Create"**
7. Aplicar a TODOS los nodos de Notion

### 1.4 Configurar IDs de Bases de Datos

Necesitás obtener el ID de "Resumen CxC":

**Método 1 - Desde Notion:**
1. Abrir "Resumen CxC" en pantalla completa
2. Copiar de la URL: `notion.so/ESTE_ES_EL_ID?v=...`

**Método 2 - Usar script:**
```bash
cd C:\Users\Gonza\Desktop\Notion-project
python -c "from create_financial_summary import *; import json; print(json.loads(requests.post('https://api.notion.com/v1/search', headers=HEADERS, json={'query': 'Resumen CxC', 'filter': {'property': 'object', 'value': 'database'}}).text)['results'][0]['id'])"
```

**Una vez que tengas el ID:**

1. En el workflow, buscar nodos:
   - "Buscar Fila Existente"
   - "Crear Fila Nueva"
2. En cada uno, reemplazar `REEMPLAZAR_CON_ID_RESUMEN_CXC` con el ID real

### 1.5 Activar Workflow

1. Click en **"Active"** (switch arriba a la derecha)
2. Verificar que diga "Active" en verde

### 1.6 Probar Webhook

1. Click derecho en nodo "Webhook - Recibir Fechas"
2. Copiar **"Production URL"**
3. Debería ser: `https://n8n.odontia.tech/webhook/calcular-cxc`

---

## 📋 PASO 2: Subir Formulario a GitHub Pages

### 2.1 Crear Repositorio en GitHub

1. Ir a https://github.com/
2. Iniciar sesión
3. Click en **"+"** → **"New repository"**
4. **Repository name:** `formulario-cxc-notion`
5. **Public** (debe ser público para GitHub Pages)
6. Click **"Create repository"**

### 2.2 Subir Formulario

1. En la página del repositorio, click **"uploading an existing file"**
2. Arrastrar el archivo `formulario_cxc.html`
3. **IMPORTANTE:** Renombrar a `index.html`
4. Commit: "Agregar formulario calculadora CxC"
5. Click **"Commit changes"**

### 2.3 Activar GitHub Pages

1. En el repositorio, ir a **"Settings"**
2. En el menú lateral, click **"Pages"**
3. En "Source":
   - Branch: **main**
   - Folder: **/ (root)**
4. Click **"Save"**
5. Esperar 1-2 minutos

### 2.4 Obtener URL del Formulario

1. Refrescar la página de Settings → Pages
2. Verás un mensaje verde: **"Your site is live at..."**
3. Copiar la URL (será algo como: `https://tuusuario.github.io/formulario-cxc-notion/`)

---

## 📋 PASO 3: Configurar CORS en n8n (Si es necesario)

Si el formulario da error de CORS:

1. En n8n, editar el nodo **"Webhook - Recibir Fechas"**
2. En "Options" → agregar:
   - **Response Headers:**
     - `Access-Control-Allow-Origin`: `*`
     - `Access-Control-Allow-Methods`: `POST, OPTIONS`
     - `Access-Control-Allow-Headers`: `Content-Type`

---

## 📋 PASO 4: Agregar Link en Notion

### En la página "Resumen CxC":

1. Abrir **"Resumen CxC"** como página completa
2. Arriba o debajo de la tabla, agregar un **Callout**:
   - Emoji: 📊
   - Color de fondo: Azul o Morado
   - Texto:
   ```
   Para calcular totales de un rango personalizado:
   👉 Click aquí → [Abrir Calculadora]
   ```
3. Seleccionar el texto "[Abrir Calculadora]"
4. Link: Pegar la URL de GitHub Pages
5. Marcar "Open in new tab"

**Ejemplo visual:**

```
┌──────────────────────────────────────────────┐
│ 📊  Para calcular rangos personalizados:    │
│     👉 [Abrir Calculadora CxC]              │
└──────────────────────────────────────────────┘
```

---

## 📋 PASO 5: Probar la Integración Completa

### Test End-to-End:

1. **En Notion:**
   - Ir a "Resumen CxC"
   - Click en el link "Abrir Calculadora"

2. **En el Formulario:**
   - Seleccionar:
     - Fecha Inicio: 01/12/2025
     - Fecha Fin: 31/12/2025
   - Click "Calcular Totales"
   - Esperar 2-3 segundos

3. **Verificar Resultado en Pantalla:**
   - Debe mostrar los totales calculados
   - Ejemplo:
     ```
     Monto Total: $XXX,XXX
     Monto Cobrado: $YY,YYY
     Saldo Pendiente: $ZZ,ZZZ
     ```

4. **Verificar en Notion:**
   - Volver a Notion
   - Refrescar (F5)
   - Ver nueva fila: "Rango: 2025-12-01 a 2025-12-31"

---

## ✅ CHECKLIST FINAL

- [ ] Workflow importado en n8n (https://n8n.odontia.tech/)
- [ ] Credenciales de Notion configuradas
- [ ] IDs de bases de datos actualizados
- [ ] Workflow activado (switch verde)
- [ ] Formulario subido a GitHub
- [ ] GitHub Pages activado
- [ ] URL del formulario obtenida
- [ ] Link agregado en Notion "Resumen CxC"
- [ ] Test completo exitoso

---

## 🎯 RESULTADO FINAL

### Para la Administración:

**Flujo de trabajo:**

1. Abren Notion → **Resumen CxC**
2. Click en **"Abrir Calculadora CxC"**
3. Se abre nueva pestaña con formulario
4. Seleccionan fechas con calendario
5. Click **"Calcular Totales"**
6. Ven resultado en pantalla (2-3 seg)
7. Vuelven a Notion y refrescan
8. ✅ Nueva fila con totales del rango

**Accesible desde:**
- ✅ Cualquier computadora
- ✅ Cualquier ubicación  
- ✅ Cualquier navegador
- ✅ 24/7 disponible

---

## 🐛 TROUBLESHOOTING

### Error: "No se puede conectar"

**Causa:** Webhook no responde

**Solución:**
1. Verificar que workflow esté **Active** en n8n
2. Verificar URL del webhook en formulario HTML
3. Ver logs de ejecución en n8n

### Error: "CORS"

**Solución:**
1. Agregar headers CORS en nodo Webhook (ver Paso 3)
2. Verificar que el dominio de GitHub Pages esté permitido

### No aparece fila en Resumen CxC

**Solución:**
1. Ver logs de ejecución en n8n
2. Verificar que ID de Resumen CxC sea correcto
3. Verificar nombres de propiedades (Período, Monto Total, etc.)

### Fechas incorrectas

**Solución:**
1. Verificar filtros en nodo "Obtener CxC Filtradas"
2. Ver que use "Fecha Emisión" correctamente

---

## 📝 MANTENIMIENTO

### Actualizar el formulario:

1. Editar `formulario_cxc.html` localmente
2. Ir al repositorio en GitHub
3. Click en `index.html`
4. Click en lápiz (Edit)
5. Pegar nuevo contenido
6. Commit changes

### Ver logs de ejecuciones:

1. En n8n → Executions
2. Ver historial completo
3. Click en ejecución para ver detalles

---

**¿Todo claro? Empezá con el Paso 1 y avisame si necesitás ayuda!** 🚀

