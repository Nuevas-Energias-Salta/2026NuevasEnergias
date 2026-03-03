# 🔄 FLUJO DE DATOS: noCRM → Trello → Notion

## VISIÓN GENERAL

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   noCRM     │ ───► │   TRELLO    │ ───► │   NOTION    │
│   (Ventas)  │      │   (Obras)   │      │   (Finanzas)│
└─────────────┘      └─────────────┘      └─────────────┘
     Lead              Proyecto             Proyecto
   "Ganado"           + Cobros              + Cliente
                                            + CxC
```

---

## 1️⃣ ESTRUCTURA EN noCRM (Lead)

### Campos requeridos al crear lead:

| Campo | Tipo | Ejemplo | Obligatorio |
|-------|------|---------|-------------|
| **Nombre Lead** | Texto | "Juan Pérez - Solar FV" | ✅ |
| **Email** | Email | juan@email.com | ✅ |
| **Teléfono** | Teléfono | +54 387 123456 | ✅ |
| **Monto Total** | Número | 1,500,000 | ✅ |
| **Monto Anticipo** | Número | 750,000 | ✅ |
| **Centro de Costo** | Dropdown | Solar/Piletas/ACS | ✅ |
| **Dirección Obra** | Texto | "Av. Bolivia 1234" | Opcional |
| **Notas** | Texto largo | Detalles del proyecto | Opcional |

### Cuando lead cambia a "GANADO":
- Trigger automático → Crea tarjeta en Trello

---

## 2️⃣ ESTRUCTURA EN TRELLO (Tarjeta)

### Campos de la tarjeta (Custom Fields):

| Campo | Tipo | Origen | Ejemplo |
|-------|------|--------|---------|
| **Nombre** | Título | Lead Name | "Juan Pérez - Solar FV" |
| **Monto Total** | Número | Lead | 1,500,000 |
| **Monto Anticipo** | Número | Lead | 750,000 |
| **Email** | Texto | Lead | juan@email.com |
| **Celular** | Número | Lead | 3871234567 |
| **Centro Costo** | Label | Lead | "Solar" (etiqueta verde) |

### Checklists de la tarjeta:

```
📋 Estado de Cobros
  □ Anticipo cobrado ($750,000)
  □ Saldo final cobrado ($750,000)

📋 Etapas del Proyecto
  □ Materiales comprados
  □ Obra iniciada
  □ Obra finalizada
  □ Postventa completada
```

### Listas de Trello:

| Lista | Significado |
|-------|-------------|
| 1 - Proyecto Nuevo | Anticipo pendiente o recién cobrado |
| 2 - En Obra | Ejecutando proyecto |
| 3 - Fin | Proyecto terminado (cobrar saldo) |
| 4 - Freezer | Cancelados/Pausados |

---

## 3️⃣ ESTRUCTURA EN NOTION (Output)

### Cuando se crea tarjeta en Trello → Se crea en Notion:

### A) CLIENTE (si no existe)

| Propiedad | Valor | Origen |
|-----------|-------|--------|
| Nombre | "Juan Pérez" | Primera parte del nombre |
| Email | juan@email.com | Custom field Trello |
| Teléfono | 3871234567 | Custom field Trello |

### B) PROYECTO

| Propiedad | Valor | Origen |
|-----------|-------|--------|
| Nombre | "Juan Pérez - Solar FV" | Nombre tarjeta |
| Cliente | → Juan Pérez | Relación |
| Centro de Costo | → Solar | Label de Trello |
| Monto Contrato | 1,500,000 | Custom field |
| Estado | "Aprobado" | Por defecto |

### C) CUENTAS POR COBRAR (2 registros)

**CxC 1 - Anticipo:**
| Propiedad | Valor |
|-----------|-------|
| Concepto | "Anticipo - Juan Pérez Solar FV" |
| Proyecto | → Proyecto creado |
| Monto Total | 750,000 (50%) |
| Monto Cobrado | 0 |
| Estado | "Pendiente" |
| Fecha Vencimiento | Fecha creación + 7 días |

**CxC 2 - Saldo Final:**
| Propiedad | Valor |
|-----------|-------|
| Concepto | "Saldo Final - Juan Pérez Solar FV" |
| Proyecto | → Proyecto creado |
| Monto Total | 750,000 (50%) |
| Monto Cobrado | 0 |
| Estado | "Pendiente" |
| Fecha Vencimiento | (se define al finalizar obra) |

---

## 4️⃣ GESTIÓN DE COBROS

### Cuando se cobra el ANTICIPO:

**En Trello:**
- ✅ Marcar "Anticipo cobrado" en checklist

**En Notion (manual o sync):**
- CxC Anticipo → Estado: "Cobrado"
- CxC Anticipo → Monto Cobrado: 750,000
- Crear registro en "Registro de Cobros"

---

### Cuando se cobra el SALDO FINAL:

**En Trello:**
- ✅ Marcar "Saldo final cobrado" en checklist
- Mover tarjeta a lista "3 - Fin"

**En Notion:**
- CxC Saldo → Estado: "Cobrado"
- CxC Saldo → Monto Cobrado: 750,000
- Proyecto → Estado: "Finalizado"

---

## 5️⃣ CÓMO SABER EL ESTADO DE COBRO

### Vista rápida en Trello:
```
Checklist vacío        = Sin cobrar
Anticipo ✅            = 50% cobrado
Anticipo ✅ + Saldo ✅ = 100% cobrado
```

### Vista en Notion (Dashboard):
- Filtrar CxC por Estado = "Pendiente"
- Ver total de saldos pendientes por cobrar

---

## 📊 MÉTRICAS DISPONIBLES

Con esta estructura podrás ver en Looker Studio:

1. **Total facturado** (suma de Monto Total de todos los proyectos)
2. **Total cobrado** (suma de Monto Cobrado de CxC)
3. **Pendiente de cobro** (Total - Cobrado)
4. **Anticipos pendientes** (CxC tipo Anticipo en estado Pendiente)
5. **Saldos finales pendientes** (CxC tipo Saldo en estado Pendiente)
6. **Cobros por mes** (gráfico de evolución)
7. **Por centro de costo** (pie chart)

---

## ⚙️ AUTOMATIZACIONES NECESARIAS

### Zapier/Make:

1. **noCRM → Trello**
   - Trigger: Lead cambia a "Ganado"
   - Action: Crear tarjeta con campos + checklist

2. **Trello → Notion**
   - Trigger: Nueva tarjeta creada
   - Actions:
     - Find/Create Cliente
     - Create Proyecto
     - Create CxC Anticipo
     - Create CxC Saldo

3. **Trello → Notion (Cobros)** [Opcional]
   - Trigger: Checklist item marcado
   - Action: Actualizar CxC correspondiente

---

## ✅ RESUMEN DE CAMBIOS NECESARIOS

### En noCRM:
- [ ] Agregar campo "Monto Anticipo" si no existe
- [ ] Agregar campo "Centro de Costo" si no existe

### En Trello:
- [ ] Crear template de tarjeta con checklist de cobros
- [ ] Verificar custom fields: Monto Total, Monto Anticipo

### En Notion:
- [ ] Agregar campo "Tipo" en CxC (Anticipo/Saldo)
- [ ] Crear vistas filtradas por tipo

### En Zapier:
- [ ] Configurar los 2-3 Zaps necesarios
