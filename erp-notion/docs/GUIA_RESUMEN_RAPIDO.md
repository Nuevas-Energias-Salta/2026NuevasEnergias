# 📊 Guía Rápida: Resumen Financiero en Notion

## ✨ Resultado Final

Vas a tener esto en tu base de datos:

```
┌──────────────────────────────────────────────┐
│  📤 Cuentas por Cobrar                       │
├──────────────────────────────────────────────┤
│                                              │
│  📊 Resumen Financiero                       │
│  ┌────────────────────────────────────────┐ │
│  │ 💰 Por Cobrar  →  Sum: $11,500,000    │ │
│  │ ✅ Cobrado     →  Sum: $8,200,000     │ │
│  │ 📊 Total       →  Sum: $19,700,000    │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  [Vista completa de la base de datos]       │
│  Concepto | Cliente | Monto | Estado        │
│  ──────────────────────────────────────      │
│  ...                                         │
└──────────────────────────────────────────────┘
```

---

## 🎯 PASO A PASO: Cuentas por Cobrar

### 1. Abrir tu base de datos
- Ve a Notion y abre **"Cuentas por Cobrar"**

### 2. Agregar espacio arriba
- Hacé clic **ARRIBA** del título de la base de datos
- Aparece un "+" cuando pasás el mouse
- O presioná Enter arriba del título

### 3. Agregar título del resumen
Escribí:
```
## 📊 Resumen Financiero
```

### 4. Crear Linked Database #1: Por Cobrar

**a) Crear el linked database:**
- Escribí `/linked` 
- Elegí "Create linked database"
- Seleccioná **"Cuentas por Cobrar"**

**b) Configurar la vista:**
- Clic en el nombre de la vista (donde dice "Cuentas por Cobrar")
- Cambiá el nombre a: **"💰 Por Cobrar"**
- Clic en **"Filter"**
- Add a filter: `Estado` → `is` → `Pendiente`
- Add filter (OR): `Estado` → `is` → `Vencido`
- En la columna "Monto", clic en el encabezado
- Calculate → **Sum**

**c) Minimizar la vista:**
- Clic en "..." (arriba derecha de esta vista)
- Properties → Desmarcá todas excepto "Monto"
- Arrastrá para hacer la vista más pequeña (solo que se vea la suma)

### 5. Crear Linked Database #2: Cobrado

Repetí el paso 4 pero:
- Nombre: **"✅ Cobrado"**
- Filtro: `Estado` → `is` → `Cobrado`
- Sum en Monto
- Minimizar

### 6. Crear Linked Database #3: Total

Repetí el paso 4 pero:
- Nombre: **"📊 Total"**
- **Sin filtros** (dejá todo)
- Sum en Monto
- Minimizar

### 7. ¡Listo! ✅

Ahora tenés los 3 números arriba de tu base de datos.

---

## 🎯 PASO A PASO: Cuentas por Pagar

Hacé **exactamente lo mismo** en tu base de datos "Cuentas por Pagar":

### Las 3 vistas a crear:

1. **"💳 Por Pagar"**
   - Filtro: `Estado` is `Pendiente` OR `Vencido`

2. **"✅ Pagado"**
   - Filtro: `Estado` is `Pagado`

3. **"📊 Total"**
   - Sin filtros

---

## 💡 Tips Extra

### Para que se vea más limpio:

**En cada linked database pequeño:**
1. Clic en "..." → "Properties"
2. Ocultá todas las columnas excepto "Concepto" y "Monto"
3. Reducí la altura para que solo se vean 1-2 filas y la suma

### Usar callouts para los números (opcional):

En lugar de linked databases, podés usar callouts y actualizar los números manualmente:

```
💰 Por Cobrar: $11,500,000
✅ Cobrado: $8,200,000
📊 Total: $19,700,000
```

Para crear callouts:
- Escribí `/callout`
- Escribí el texto con el número
- Actualizá manualmente cuando cambien los datos

---

## 🎨 Personalización

### Iconos recomendados:
- 💰 Por Cobrar / Por Pagar
- ✅ Cobrado / Pagado
- 📊 Total
- ⚠️ Vencido (opcional)

### Colores:
- Callout verde para "Cobrado/Pagado"
- Callout amarillo para "Pendiente"
- Callout rojo para "Vencido"

---

## ✅ Checklist

**Cuentas por Cobrar:**
- [ ] Agregar espacio arriba de la base de datos
- [ ] Agregar título "📊 Resumen Financiero"
- [ ] Crear linked database "💰 Por Cobrar" (filtrado)
- [ ] Crear linked database "✅ Cobrado" (filtrado)
- [ ] Crear linked database "📊 Total" (sin filtro)
- [ ] Minimizar las 3 vistas
- [ ] Activar Sum en todas

**Cuentas por Pagar:**
- [ ] Repetir lo mismo
- [ ] Crear "💳 Por Pagar"
- [ ] Crear "✅ Pagado"
- [ ] Crear "📊 Total"

---

## 🚀 Resultado

Ahora cuando abras "Cuentas por Cobrar" o "Cuentas por Pagar", vas a ver inmediatamente:
- ¿Cuánto te deben / debés?
- ¿Cuánto ya cobraste / pagaste?
- ¿Cuál es el total general?

Todo actualizado automáticamente por Notion 🎉

---

## ❓ Problemas comunes

**P: Los filtros no funcionan**
- Asegurate de usar "OR" entre Pendiente y Vencido, no "AND"

**P: No veo la suma**
- Clic en encabezado "Monto" → Calculate → Sum

**P: Las vistas son muy grandes**
- Ocultá columnas innecesarias en Properties
- Arrastrá el borde inferior para achicar la altura

**P: Quiero copiar esto a otra página**
- Podés hacer duplicate del bloque completo (linked databases incluidos)

¡Cualquier duda, avisame! 💪
