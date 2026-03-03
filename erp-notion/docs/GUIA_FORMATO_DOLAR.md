# 💵 Guía Paso a Paso: Agregar $ a Todas las Columnas de Monto

## 🎯 Objetivo
Cambiar todas las columnas de monto para que muestren **$300.000,00** en lugar de solo números.

---

## 📋 PARTE 1: Cuentas por Cobrar

### ✅ COLUMNA 1: Monto (en CxC)

**Paso 1:** Abrir Cuentas por Cobrar en Notion

**Paso 2:** Renombrar la columna "Monto"
1. Hacer clic en el encabezado de la columna **"Monto"**
2. Seleccionar **"Edit property"**
3. Cambiar el nombre a: **"Monto Base"**
4. Guardar

**Paso 3:** Crear nueva columna "Monto" con formato $
1. Hacer clic en **"+"** para agregar nueva columna
2. Tipo de columna: **"Formula"**
3. Nombre: **"Monto"**
4. En el campo de fórmula, pegar esto:

```
lets(
  amount, prop("Monto Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

5. Guardar

**Paso 4:** Ocultar "Monto Base"
1. Hacer clic en **"..."** (arriba a la derecha de la tabla)
2. Seleccionar **"Properties"**
3. Desmarcar la casilla de **"Monto Base"**
4. Cerrar

**✅ RESULTADO:** Ahora "Monto" muestra $300.000,00

---

### ✅ COLUMNA 2: Monto Cobrado (en CxC)

> **NOTA:** "Monto Cobrado" es un **rollup** (suma desde otra tabla).
> Los rollups NO se pueden convertir a fórmula directamente.

**Opción A - Simple:** Dejar como está (ya tiene formato numérico)

**Opción B - Crear columna formateada:**

**Paso 1:** Renombrar "Monto Cobrado"
1. Clic en encabezado **"Monto Cobrado"**
2. Edit property → Cambiar a **"Monto Cobrado Base"**
3. Guardar

**Paso 2:** Crear nueva columna "Monto Cobrado"
1. Nueva columna → Tipo: **Formula**
2. Nombre: **"Monto Cobrado"**
3. Fórmula:

```
lets(
  amount, prop("Monto Cobrado Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

4. Ocultar "Monto Cobrado Base" en Properties

---

### ✅ YA HECHO: Saldo Pendiente
**Esta columna ya tiene formato $ - No hacer nada** ✓

---

## 📋 PARTE 2: Cuentas por Pagar

### ✅ COLUMNA 3: Monto (en CxP)

**Paso 1:** Abrir Cuentas por Pagar en Notion

**Paso 2:** Renombrar "Monto" a "Monto Base"

**Paso 3:** Crear nueva columna "Monto" (Formula)

**Fórmula:**
```
lets(
  amount, prop("Monto Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

**Paso 4:** Ocultar "Monto Base"

---

### ✅ COLUMNA 4: Monto Pagado (en CxP)

Similar a "Monto Cobrado" en CxC (es rollup):

**Paso 1:** Renombrar a "Monto Pagado Base"

**Paso 2:** Crear "Monto Pagado" (Formula)

**Fórmula:**
```
lets(
  amount, prop("Monto Pagado Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

**Paso 3:** Ocultar "Monto Pagado Base"

---

### ✅ COLUMNA 5: Saldo Pendiente (en CxP)

**Si NO existe aún:**

**Paso 1:** Crear columna "Saldo Pendiente" (Formula)

**Fórmula:**
```
lets(
  pendingAmount, prop("Monto Base") - prop("Monto Pagado Base"),
  amountStr, format(round(pendingAmount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

---

## 📋 PARTE 3: Proyectos/Obras

### ✅ COLUMNA 6: Monto Contrato

**Paso 1:** Abrir Proyectos/Obras en Notion

**Paso 2:** Renombrar "Monto Contrato" a "Monto Contrato Base"

**Paso 3:** Crear nueva "Monto Contrato" (Formula)

**Fórmula:**
```
lets(
  amount, prop("Monto Contrato Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

**Paso 4:** Ocultar "Monto Contrato Base"

---

## 📋 PARTE 4: Resumen CxC

### ✅ COLUMNAS 7, 8, 9: Todas las columnas

En "Resumen CxC" hay 3 columnas numéricas. Para cada una:

**Columnas:**
- Monto Total
- Monto Cobrado  
- Saldo Pendiente

**Para CADA una:**

1. Renombrar a "[Nombre] Base"
2. Crear nueva con fórmula (reemplazar el `prop()` con el nombre base):

```
lets(
  amount, prop("[Nombre] Base"),
  amountStr, format(round(amount, 2)),
  parts, amountStr.split("."),
  integerPart, parts.first(),
  decimalPart, if(parts.length() > 1, parts.last().padEnd(2, "0"), "00"),
  formattedInteger, integerPart.replaceAll("(\\d)(?=(\\d{3})+$)", "$1."),
  
  "$" + formattedInteger + "," + decimalPart
)
```

3. Ocultar columna Base

---

## 📋 PARTE 5: Resumen CxP

### ✅ COLUMNAS 10, 11, 12: Todas las columnas

Mismo proceso que Resumen CxC:

**Columnas:**
- Monto Total
- Monto Pagado
- Saldo Pendiente

Aplicar la misma fórmula cambiando el nombre en `prop()`.

---

## ✅ Checklist Final

- [ ] CxC: Monto
- [ ] CxC: Monto Cobrado  
- [ ] CxC: Saldo Pendiente (ya hecho)
- [ ] CxP: Monto
- [ ] CxP: Monto Pagado
- [ ] CxP: Saldo Pendiente
- [ ] Proyectos: Monto Contrato
- [ ] Resumen CxC: Monto Total
- [ ] Resumen CxC: Monto Cobrado
- [ ] Resumen CxC: Saldo Pendiente
- [ ] Resumen CxP: Monto Total
- [ ] Resumen CxP: Monto Pagado
- [ ] Resumen CxP: Saldo Pendiente

---

## 💡 Tips

1. **Copiar la fórmula:** Seleccionar todo el bloque de código y Ctrl+C
2. **Pegar en Notion:** Ctrl+V en el campo de fórmula
3. **Editar `prop()`:** Solo cambiar el nombre dentro de `prop("Nombre Base")`
4. **Si hay error:** Verificar comillas y paréntesis

---

## ⚠️ Importante

- **NO borres** las columnas "Base" - solo ocultarlas
- Los scripts de auto-generación seguirán escribiendo a las columnas "Base"
- Las columnas formateadas solo MUESTRAN, no almacenan datos

---

## 🚀 Orden Recomendado

1. Empezar con **Cuentas por Cobrar - Monto**
2. Verificar que funciona
3. Continuar con las demás una por una

¡Avisame cuando termines cada una y yo te ayudo si hay algún problema! 💪
