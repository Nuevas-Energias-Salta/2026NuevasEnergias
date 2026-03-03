# 🔗 Opción C2: Link con Webhook en Notion

## 🎯 Solución Implementada

Link clickeable en Notion → Abre formulario HTML → Llama webhook n8n → Actualiza Resumen CxC

---

## 📋 PASO 1: Configurar Webhook en n8n

### 1.1 Crear Workflow

1. Abrir n8n
2. Crear nuevo workflow
3. Agregar nodo **"Webhook"**
4. Configurar:
   - **HTTP Method:** POST
   - **Path:** `calcular-rango-cxc`
   - **Response Mode:** Respond Immediately
5. Copiar la **Webhook URL** (algo como: `http://localhost:5678/webhook/calcular-rango-cxc`)

### 1.2 Agregar Nodos de Procesamiento

Después del Webhook, agregar estos nodos en orden:

**Nodo 2: Function - Extraer Fechas**
```javascript
const fechaInicio = $json.body.fechaInicio;
const fechaFin = $json.body.fechaFin;

return {
  json: {
    fechaInicio,
    fechaFin
  }
};
```

**Nodo 3: Notion - Obtener CxC Filtradas**
- Resource: Database Page
- Operation: Get All
- Database ID: `2e0c81c3-5804-815a-8755-f4f254257f6a` (CxC)
- Filters:
  - Fecha Emisión → on or after → `{{$json.fechaInicio}}`
  - Fecha Emisión → on or before → `{{$json.fechaFin}}`

**Nodo 4: Function - Calcular Totales**
```javascript
let totalMonto = 0;
let totalCobrado = 0;

for (const item of items) {
  const monto = item.json.properties['Monto Base']?.number || 
                item.json.properties['Monto']?.number || 0;
  
  const cobradoProp = item.json.properties['Monto Cobrado Base'] || 
                      item.json.properties['Monto Cobrado'];
  let cobrado = 0;
  
  if (cobradoProp?.type === 'rollup') {
    cobrado = cobradoProp.rollup?.number || 0;
  } else {
    cobrado = cobradoProp?.number || 0;
  }
  
  totalMonto += monto;
  totalCobrado += cobrado;
}

const totalPendiente = totalMonto - totalCobrado;
const fechaInicio = $node["Function"].json.fechaInicio;
const fechaFin = $node["Function"].json.fechaFin;

return [{
  json: {
    montoTotal: totalMonto,
    montoCobrado: totalCobrado,
    saldoPendiente: totalPendiente,
    periodo: `Rango: ${fechaInicio} a ${fechaFin}`,
    fechaInicio,
    fechaFin
  }
}];
```

**Nodo 5: Buscar Fila Existente en Resumen CxC**
- Resource: Database Page
- Operation: Get All
- Database ID: [ID de Resumen CxC]
- Filter: Período → equals → `{{$json.periodo}}`

**Nodo 6: IF - ¿Existe fila?**
- Condition: `{{$json.id}}` → is not empty

**Nodo 7a: Notion - Actualizar Fila** (si existe)
- Resource: Page
- Operation: Update
- Page ID: `{{$json.id}}`
- Properties:
  - Monto Total: `{{$node["Function 1"].json.montoTotal}}`
  - Monto Cobrado: `{{$node["Function 1"].json.montoCobrado}}`
  - Saldo Pendiente: `{{$node["Function 1"].json.saldoPendiente}}`

**Nodo 7b: Notion - Crear Fila** (si no existe)
- Resource: Page
- Operation: Create
- Database ID: [ID de Resumen CxC]
- Properties:
  - Período: `{{$node["Function 1"].json.periodo}}`
  - Monto Total: `{{$node["Function 1"].json.montoTotal}}`
  - Monto Cobrado: `{{$node["Function 1"].json.montoCobrado}}`
  - Saldo Pendiente: `{{$node["Function 1"].json.saldoPendiente}}`

**Nodo 8: Respond to Webhook**
- Response Mode: Respond When Last Node Finishes
- Respond With: JSON
- JSON:
```json
{
  "montoTotal": "={{$node[\"Function 1\"].json.montoTotal}}",
  "montoCobrado": "={{$node[\"Function 1\"].json.montoCobrado}}",
  "saldoPendiente": "={{$node[\"Function 1\"].json.saldoPendiente}}"
}
```

### 1.3 Activar Workflow

Hacer clic en **"Active"** arriba a la derecha

---

## 📋 PASO 2: Hostear el Formulario HTML

### Opción A: Servidor Local Simple (Recomendado para testing)

1. Abrir terminal en: `C:\Users\Gonza\Desktop\Notion-project`
2. Ejecutar:
```bash
python -m http.server 8000
```
3. El formulario estará en: `http://localhost:8000/formulario_cxc.html`

### Opción B: Hostear en Servidor Web Real

Si tenés servidor web:
- Subir `formulario_cxc.html` al servidor
- URL será algo como: `https://tuservidor.com/formulario_cxc.html`

---

## 📋 PASO 3: Actualizar URL del Webhook

1. Abrir `formulario_cxc.html` en editor de texto
2. Buscar línea 183:
```javascript
const WEBHOOK_URL = 'http://localhost:5678/webhook/calcular-rango-cxc';
```
3. Reemplazar con la URL real del webhook de n8n
4. Guardar archivo

---

## 📋 PASO 4: Agregar Link en Notion

### En la página "Resumen CxC":

1. Crear un callout o bloque de texto:
```
📊 Para calcular totales de un rango personalizado:
👉 [Click aquí para abrir calculadora](http://localhost:8000/formulario_cxc.html)
```

2. O crear botón más visual:
   - Crear toggle/callout con fondo de color
   - Texto: "🔗 Calcular Rango Personalizado"
   - Link: URL del formulario

### Alternativa: Crear página dedicada

1. Crear página "Calculadora CxC"
2. Agregar el link al formulario
3. Vincular desde Resumen CxC

---

## 🚀 USO PARA LA ADMINISTRACIÓN

### Proceso completo:

1. **Ir a Resumen CxC** en Notion
2. **Hacer clic** en el link "Calcular Rango Personalizado"
3. Se abre el formulario en nueva pestaña
4. **Seleccionar fechas** con los calendarios
5. **Click en "Calcular Totales"**
6. Esperar 2-3 segundos
7. ✅ **Ver resultados** en pantalla
8. **Volver a Notion** y refrescar (F5)
9. ✅ **Ver nueva fila** en Resumen CxC con el período calculado

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Permitir Acceso desde Otras PCs (LAN)

Si querés que otros en la red puedan usar:

1. Encontrar tu IP local:
```bash
ipconfig
```
Buscar "IPv4 Address" (ej: 192.168.1.100)

2. En el formulario, cambiar URL a:
```javascript
const WEBHOOK_URL = 'http://192.168.1.100:5678/webhook/calcular-rango-cxc';
```

3. Hostear formulario para que sea accesible:
   - Usar servidor web real (Apache, Nginx)
   - O compartir carpeta en red

4. URL del formulario será: `http://192.168.1.100:8000/formulario_cxc.html`

### Agregar Autenticación (Opcional)

Si querés proteger el webhook:

1. En n8n, agregar nodo "HTTP Request Header Auth"
2. En formulario, agregar header:
```javascript
headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer TU_TOKEN_SECRETO'
}
```

---

## 🐛 TROUBLESHOOTING

**Error: "No se puede conectar al webhook"**
- Verificar que n8n esté corriendo
- Verificar que el workflow esté **Active**
- Ver si la URL del webhook es correcta

**Error: "CORS"**
- Agregar header en n8n webhook:
  ```
  Access-Control-Allow-Origin: *
  ```

**No aparece fila en Resumen CxC**
- Verificar ID de base de datos en workflow
- Ver logs de n8n para errores
- Verificar nombres de propiedades (Monto Base, etc.)

**Formulario se cierra solo**
- Normal si es popup. Abrir en nueva pestaña completa
- O agregar botón "Cerrar" en formulario

---

## ✅ VERIFICACIÓN

Lista de chequeo:

- [ ] n8n corriendo y workflow active
- [ ] Webhook URL configurada en formulario
- [ ] Formulario accesible desde navegador
- [ ] Link agregado en Notion
- [ ] Test exitoso (click → calcular → ver fila en Resumen)

---

## 📝 BONUS: Mejorar UX

### Agregar más períodos pre-definidos:

En el formulario, agregar botones:

```html
<button type="button" onclick="setEstaSemana()">Esta Semana</button>
<button type="button" onclick="setEsteMes()">Este Mes</button>
<button type="button" onclick="setTrimestre()">Este Trimestre</button>
```

```javascript
function setEstaSemana() {
    // Código para calcular inicio y fin de semana actual
}
```

---

**¿Listo para probarlo? Configurá el webhook en n8n primero y avisame cuando lo tengas!** 🚀
