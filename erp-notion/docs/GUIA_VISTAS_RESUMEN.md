# Guía: Configurar Vistas de Resumen en Notion

## 📊 Resumen

Esta guía explica cómo configurar vistas con sumas de montos en las bases de datos de **Cuentas por Cobrar** y **Cuentas por Pagar** en Notion.

---

## 🎯 Objetivos de las Vistas

### Cuentas por Cobrar (CxC)
Necesitas ver:
1. **Suma de Monto Total**: Todo lo facturado
2. **Suma de Monto Pendiente**: Lo que falta cobrar
3. **Suma de Monto Cobrado**: Lo que ya se cobró

### Cuentas por Pagar (CxP)
Lo mismo para CxP:
1. **Suma de Monto Total**: Todo lo que debés pagar
2. **Suma de Monto Pendiente**: Lo que falta pagar
3. **Suma de Monto Pagado**: Lo que ya se pagó

---

## 📍 Método 1: Activar Suma en la Vista Existente

Esta es la forma más simple y **NO requiere código**.

### Para Cuentas por Cobrar:

1. **Abrir la base de datos** "Cuentas por Cobrar" en Notion
2. **Habilitar Calculate en la columna Monto:**
   - Hacer clic en el encabezado de la columna "Monto"
   - Seleccionar "Calculate" o "Calcular"
   - Elegir **"Sum"** (Suma)
   - Verás el total al pie de la columna

3. **Crear vistas filtradas para ver los subtotales:**

#### Vista: "Todo por Cobrar"
- Filtro: `Estado` is `Pendiente` OR `Estado` is `Vencido`
- Esto te mostrará solo lo que falta cobrar
- La suma al pie = Total por Cobrar

#### Vista: "Cobrado"
- Filtro: `Estado` is `Cobrado`
- La suma al pie = Total Cobrado

#### Vista: "Todas las Cuentas"
- Sin filtros
- La suma al pie = Monto Total

### Para Cuentas por Pagar:

Mismo proceso pero con los estados de CxP:

#### Vista: "Todo por Pagar"  
- Filtro: `Estado` is `Pendiente` OR `Estado` is `Vencido`
- Suma al pie = Total por Pagar

#### Vista: "Pagado"
- Filtro: `Estado` is `Pagado`
- Suma al pie = Total Pagado

#### Vista: "Todas las Cuentas"
- Sin filtros
- Suma al pie = Monto Total

---

## 📍 Método 2: Crear Vista de Tablero (Board)

Para una visualización más clara:

### Cuentas por Cobrar:

1. En la esquina superior derecha, clic en **"+ Add a view"**
2. Elegir **"Board"** (Tablero)
3. Nombre: "Resumen por Estado"
4. Group by: `Estado`
5. En cada columna verás agrupadas las cuentas
6. Habilitar "Calculate" → "Sum" en la columna Monto

Ahora tendrás columnas como:
- **Pendiente**: $X,XXX,XXX
- **Cobrado**: $X,XXX,XXX
- **Vencido**: $X,XXX,XXX

### Cuentas por Pagar:

Mismo proceso, agrupando por `Estado`.

---

## 📍 Método 3: Crear Dashboard con Linked Databases

Para tener todo en una página:

1. **Crear una página nueva**: "Dashboard Financiero"

2. **Agregar Linked Database para CxC:**
   - Escribir `/linked` y elegir "Cuentas por Cobrar"
   - Crear 3 vistas diferentes en esta linked database:

   **Vista 1: "Por Cobrar"**
   - Filtro: Estado = Pendiente o Vencido
   - Sum en Monto

   **Vista 2: "Cobrado"**
   - Filtro: Estado = Cobrado
   - Sum en Monto

   **Vista 3: "Total"**
   - Sin filtros
   - Sum en Monto

3. **Agregar Linked Database para CxP:**
   - Mismo proceso

4. **Agregar Callouts con totales:**
   - Escribir `/callout`
   - Copiar manualmente los totales de las sumas
   - Actualizar periódicamente

---

## 🎨 Configuración Visual Recomendada

### Layout sugerido para Dashboard:

```
┌─────────────────────────────────────────┐
│     🏦 DASHBOARD FINANCIERO             │
├─────────────────────────────────────────┤
│                                         │
│  📤 CUENTAS POR COBRAR                  │
│  ┌──────────────┬──────────────────┐   │
│  │ Por Cobrar   │ $XX,XXX,XXX      │   │
│  │ Cobrado      │ $XX,XXX,XXX      │   │
│  │ Total        │ $XX,XXX,XXX      │   │
│  └──────────────┴──────────────────┘   │
│                                         │
│  [Linked Database - Vista detallada]   │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  📥 CUENTAS POR PAGAR                   │
│  ┌──────────────┬──────────────────┐   │
│  │ Por Pagar    │ $XX,XXX,XXX      │   │
│  │ Pagado       │ $XX,XXX,XXX      │   │
│  │ Total        │ $XX,XXX,XXX      │   │
│  └──────────────┴──────────────────┘   │
│                                         │
│  [Linked Database - Vista detallada]   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📊 Paso a Paso Detallado: Activar Sumas

### En Cuentas por Cobrar:

1. Abrir "Cuentas por Cobrar"
2. Clic en el **encabezado** de la columna "Monto" (donde dice "Monto")
3. En el menú que aparece, buscar **"Calculate"**
4. Seleccionar **"Sum"**
5. ✅ Ahora verás la suma total al pie de la columna

### Repetir para filtrar por estado:

6. Clic en **"Filter"** (arriba a la derecha)
7. **Add a filter**
8. Seleccionar: `Estado` → `is` → `Pendiente`
9. Agregar otro filtro (con OR): `Estado` → `is` → `Vencido`
10. ✅ La suma ahora muestra solo lo pendiente

11. Guardar esta vista:
    - Clic en el nombre de la vista (arriba)
    - "Duplicate view"
    - Renombrar a "Por Cobrar"

12. Crear otra vista para "Cobrado":
    - Mismos pasos pero filtro: `Estado` → `is` → `Cobrado`

---

## 💡 Tips Adicionales

### Ordenamiento útil:
- **Por Fecha Vencimiento** (ascendente): Ver lo más urgente primero
- **Por Estado** + **Por Monto** (descendente): Ver los montos grandes pendientes

### Colores condicionales:
Notion agrupa automáticamente por colores según estado:
- 🟡 Amarillo = Pendiente
- 🔴 Rojo = Vencido
- 🟢 Verde = Cobrado/Pagado

### Multi-select en Calculate:
Puedes habilitar "Calculate" en varias columnas:
- **Monto**: Sum
- **Cantidad de cuentas**: Count all

---

## ⚠️ Limitaciones de Notion API

> [!NOTE]
> **Las vistas NO se pueden crear por API**, por eso esta guía es manual. Sin embargo, una vez creadas, las vistas se mantienen automáticamente.

> [!TIP]
> **Crea las vistas una sola vez** y luego simplemente cambia entre ellas para ver diferentes totales.

---

## 🎓 Ejemplo Práctico

### Escenario: Ver cuánto falta cobrar

1. Ir a "Cuentas por Cobrar"
2. Crear vista "Por Cobrar" con filtros:
   - Estado = Pendiente OR Vencido
3. Activar Sum en columna Monto
4. **Resultado**: Ves todas las facturas pendientes y el total a cobrar

**Ejemplo visual:**
```
Concepto              | Cliente   | Monto        | Estado
──────────────────────|─────────--|─────────────|──────────
Anticipo Proyecto A   | Cliente 1 | $2,400,000  | Pendiente
Cuota 2 Proyecto B    | Cliente 2 | $7,500,000  | Vencido
Saldo Final Proyecto C| Cliente 3 | $1,600,000  | Pendiente
──────────────────────|─────────--|─────────────|──────────
                      | Sum:      | $11,500,000 |
```

---

## ✅ Checklist de Configuración

### Cuentas por Cobrar:
- [ ] Activar Sum en columna "Monto"
- [ ] Crear vista "Por Cobrar" (Pendiente + Vencido)
- [ ] Crear vista "Cobrado"  
- [ ] Crear vista "Todas" (sin filtros)
- [ ] (Opcional) Crear Board agrupado por Estado

### Cuentas por Pagar:
- [ ] Activar Sum en columna "Monto"
- [ ] Crear vista "Por Pagar" (Pendiente + Vencido)
- [ ] Crear vista "Pagado"
- [ ] Crear vista "Todas" (sin filtros)
- [ ] (Opcional) Crear Board agrupado por Estado

### Dashboard (Opcional):
- [ ] Crear página "Dashboard Financiero"
- [ ] Agregar Linked Database de CxC
- [ ] Agregar Linked Database de CxP
- [ ] Configurar vistas en cada linked database

---

## 🔍 Solución de Problemas

**P: No veo la opción "Calculate"**  
R: Asegúrate de hacer clic en el encabezado de la columna, no en una celda.

**P: La suma no se actualiza**  
R: Notion actualiza automáticamente. Si no se actualiza, recarga la página (F5).

**P: ¿Puedo ver los 3 totales a la vez?**  
R: No en una sola vista. Necesitas crear 3 vistas diferentes o usar Linked Databases en un dashboard.

**P: ¿Cómo exporto estos totales?**  
R: Notion no exporta las sumas directamente, pero puedes copiar manualmente o usar la API para calcular.

---

## 🚀 Próximo Nivel: Automatización (Avanzado)

Si querés automatizar completamente, puedes:

1. **Crear un script Python** que consulte Notion y calcule los totales
2. **Actualizar un Dashboard en Notion** con los totales usando la API
3. **Generar reportes periódicos** automáticamente

> Consulta el archivo `create_financial_summary.py` (si exists) para scripts de automatización.

---

## 📝 Resumen Final

**Lo más simple:**
1. Abrir base de datos
2. Clic en encabezado "Monto"
3. Calculate → Sum
4. Crear vistas filtradas por Estado

**Lo más completo:**
- Crear Dashboard Financiero
- Múltiples Linked Databases
- Vistas específicas por necesidad

¡Con esto tendrás visibilidad completa de tu flujo de caja en Notion! 💰
