# Sistema de Asignación de Pagos - CxP

## Diagrama de Relaciones

```mermaid
flowchart TB
    subgraph PAGOS["📋 Registro de Pagos"]
        P1["Pago #1<br/>Monto: $500"]
        P2["Pago #2<br/>Monto: $1,000"]
    end
    
    subgraph ASIGNACIONES["🔗 Asignaciones de Pagos"]
        A1["Asignación 1<br/>$200 → Factura A"]
        A2["Asignación 2<br/>$300 → Factura B"]
        A3["Asignación 3<br/>$800 → Factura C"]
    end
    
    subgraph CXP["📄 Cuentas por Pagar"]
        F1["Factura A<br/>Monto: $200<br/>Saldo: $0 ✅"]
        F2["Factura B<br/>Monto: $500<br/>Saldo: $200"]
        F3["Factura C<br/>Monto: $800<br/>Saldo: $0 ✅"]
    end
    
    P1 --> A1
    P1 --> A2
    P2 --> A3
    
    A1 --> F1
    A2 --> F2
    A3 --> F3
```

---

## Flujo del Proceso

```mermaid
flowchart LR
    A["1️⃣ Registrar Pago"] --> B["2️⃣ Vincular Facturas"]
    B --> C["3️⃣ Workflow Automático"]
    C --> D["4️⃣ Crear Asignaciones"]
    D --> E["5️⃣ Actualizar Saldos"]
    E --> F["6️⃣ Marcar Pagadas"]
```

---

## Bases de Datos Involucradas

| Base de Datos | Función |
|---------------|---------|
| **Registro de Pagos** | Donde se registra cada pago realizado |
| **Asignaciones de Pagos** | Detalle de cuánto de cada pago va a cada factura |
| **Cuentas por Pagar** | Las facturas/deudas pendientes |

---

## Campos Clave

### Registro de Pagos
- Monto (total del pago)
- Cuenta Por Pagar (facturas vinculadas)
- Total Asignado (rollup - suma de asignaciones)
- Saldo a Favor (Monto - Total Asignado)

### Asignaciones de Pagos
- Monto Asignado (porción del pago para esta factura)
- Pago (relación al pago origen)
- CxP (relación a la factura destino)

### Cuentas por Pagar
- Monto base (valor de la factura)
- Monto Asignado Total (rollup - suma de asignaciones)
- Saldo Pendiente (Monto base - Monto Asignado Total)

---

## Ejemplo Práctico

**Situación:** 
- Factura A: $200
- Factura B: $500  
- Factura C: $800

**Se realiza un pago de $700 vinculando las 3 facturas:**

| Factura | Monto | Asignado | Saldo | Estado |
|---------|-------|----------|-------|--------|
| A | $200 | $200 | $0 | Pagado ✅ |
| B | $500 | $500 | $0 | Pagado ✅ |
| C | $800 | $0 | $800 | Pendiente |

El sistema asigna automáticamente en orden de fecha (FIFO).
