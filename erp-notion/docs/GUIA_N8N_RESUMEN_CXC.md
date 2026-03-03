# 🔄 Automatización n8n para Resumen CxC

## 🎯 Objetivo

Permitir que la administración calcule totales de rangos de fechas personalizados directamente desde Notion, sin ejecutar scripts.

---

## 📋 Requisitos

- n8n instalado y corriendo
- Cuenta de Notion con acceso a API

---

## 🏗️ PASO 1: Crear Tabla de Solicitudes en Notion

### En Notion:

1. Ir a **Gestión Financiera** o crear nueva página
2. Crear nueva tabla: **"Solicitar Cálculo CxC"**
3. Agregar propiedades:
   - **Fecha Inicio** (tipo: Date)
   - **Fecha Fin** (tipo: Date)
   - **Estado** (tipo: Select) con opciones:
     - Pendiente
     - Procesado

4. Copiar el **ID de esta base de datos**:
   - Abrir la tabla en pantalla completa
   - Copiar de la URL: `notion.so/ESTE_ES_EL_ID/...`

---

## 🔧 PASO 2: Configurar n8n

### 2.1 Importar Workflow

1. Abrir n8n
2. **Workflows** → **Import from File**
3. Seleccionar: `n8n_workflow_resumen_cxc.json`

### 2.2 Configurar Credenciales Notion

1. En n8n, crear **Credential** de Notion
2. Agregar tu **Integration Token**: `YOUR_NOTION_TOKEN_HERE`
3. Guardar

### 2.3 Reemplazar IDs

En el workflow importado, editar estos nodos reemplazando los IDs:

**Nodo "Notion - Leer Solicitudes":**
- `databaseId`: ID de la tabla "Solicitar Cálculo CxC" (del Paso 1)

**Nodo "Buscar Fila Existente":**
- `databaseId`: ID de "Resumen CxC"
  - Para obtenerlo: Buscar en Notion con el script o manualmente

**Nodo "Crear Fila Nueva":**
- `databaseId`: ID de "Resumen CxC" (mismo que arriba)

### 2.4 Configurar Trigger

Opciones:

**Opción A - Manual:**
- Agregar nodo "Manually Trigger" al inicio
- Ejecutar manualmente cuando quieras

**Opción B - Programado:**
- Agregar nodo "Schedule Trigger"
- Configurar: cada 15 minutos o cada hora
- El workflow busca solicitudes "Pendientes" automáticamente

**Opción C - Webhook (recomendado):**
- Agregar nodo "Webhook"
- Copiar la URL del webhook
- En Notion, usar Automation (si disponible) o botón personalizado

---

## 🚀 PASO 3: Usar el Sistema

### Para la Administración:

1. Abrir tabla **"Solicitar Cálculo CxC"** en Notion
2. Agregar nueva fila:
   - **Fecha Inicio:** 01/12/2025
   - **Fecha Fin:** 31/12/2025
   - **Estado:** Pendiente
3. Guardar

### Automáticamente:

1. n8n detecta la solicitud (si está programado) o ejecutar manual
2. Calcula los totales
3. Crea/actualiza fila en **Resumen CxC**:
   - Período: "Rango: 2025-12-01 a 2025-12-31"
   - Monto Total, Monto Cobrado, Saldo Pendiente
4. Marca la solicitud como **"Procesado"**

---

## 📊 Flujo del Workflow

```
1. Leer Solicitudes (Estado = Pendiente)
   ↓
2. Obtener CxC filtradas por fechas
   ↓
3. Calcular totales (Monto, Cobrado, Pendiente)
   ↓
4. Buscar si ya existe fila para ese rango
   ↓
5. Actualizar fila existente O Crear nueva
   ↓
6. Marcar solicitud como Procesada
```

---

## ⚙️ Configuración Avanzada

### Ejecutar automáticamente cada hora:

1. En n8n, agregar nodo **"Schedule Trigger"**
2. Configurar: `0 * * * *` (cada hora en punto)
3. Conectar al workflow

### Notificar cuando termine:

1. Agregar nodo **"Send Email"** al final
2. O nodo **"Slack"** si usás Slack
3. Mensaje: "Cálculo completado para rango X"

---

## ✅ Verificación

Después de configurar:

1. Crear solicitud de prueba en Notion
2. Ejecutar workflow manualmente en n8n
3. Verificar que aparece fila en Resumen CxC
4. Verificar que solicitud cambió a "Procesado"

---

## 🎁 Bonus: Mejorar UX

### Crear botón visual en Notion:

Aunque Notion no tiene botones reales, podés:

1. Crear página "📅 Solicitar Análisis"
2. Dentro, explicar cómo usar la tabla
3. Agregar template de fila con fechas pre-llenadas

### Ejemplos de plantillas:

- "Esta Semana" (lunes actual - domingo)
- "Este Mes" (día 1 - último día)
- "Último Trimestre"

---

## 🐛 Troubleshooting

**"No se crean filas en Resumen CxC":**
- Verificar IDs de bases de datos
- Verificar credenciales de Notion
- Ver logs en n8n

**"Solicitudes quedan en Pendiente":**
- Verificar que el workflow se ejecutó
- Ver si hay errores en nodos de n8n

**"Totales incorrectos":**
- Verificar nombres de propiedades en función de cálculo
- Verificar que "Monto Base" y "Monto Cobrado Base" existen

---

## 📝 Notas

- El workflow procesa TODAS las solicitudes pendientes
- Si hay múltiples solicitudes, crea múltiples filas
- Las filas se identifican por el texto del "Período"
- Si ejecutás dos veces el mismo rango, actualiza la fila existente

---

**¿Necesitás ayuda con la configuración? Avisame en qué paso estás!** 🚀

