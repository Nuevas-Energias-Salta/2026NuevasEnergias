# Guía de Registro de Pagos - Administración

## ¿Cómo registrar un pago?

### Paso 1: Ir a "Registro de Pagos"
- En Notion, abrir la base de datos **"Registro de Pagos"**

### Paso 2: Crear nuevo pago
- Click en **"+ Nuevo"**
- Completar los campos:
  - **Concepto**: Descripción del pago (ej: "Pago materiales enero")
  - **Monto**: Monto total del pago
  - **Fecha Pago**: Fecha en que se realizó
  - **Método de Pago**: Transferencia, Cheque, Efectivo, etc.
  - **Comprobante**: Número de comprobante (opcional)

### Paso 3: Vincular las facturas (CxP)
- En el campo **"Cuenta Por Pagar"**, seleccionar las facturas que cubre este pago
- Podés seleccionar **una o varias** facturas

### Paso 4: Guardar y esperar
- Guardar el registro
- **Esperar ~1 minuto** (el sistema procesa automáticamente)

---

## ¿Qué pasa automáticamente?

1. El sistema **distribuye el monto** entre las facturas seleccionadas (por orden de fecha)
2. **Actualiza el saldo pendiente** de cada factura
3. Si una factura queda completamente cubierta, la marca como **"Pagado"**

---

## ¿Dónde ver los resultados?

| Base de datos | Qué ver |
|---------------|---------|
| **Cuentas por Pagar** | Columna "Saldo Pendiente" actualizada |
| **Asignaciones de Pagos** | Detalle de cuánto fue a cada factura |

---

## Ejemplo práctico

**Situación:** Tengo 3 facturas pendientes:
- Factura A: $200
- Factura B: $300
- Factura C: $400

**Acción:** Registro un pago de $500 y selecciono las 3 facturas.

**Resultado automático:**
- Factura A: Recibe $200 → Saldo: $0 → Estado: Pagado ✅
- Factura B: Recibe $300 → Saldo: $0 → Estado: Pagado ✅
- Factura C: No alcanzó → Saldo: $400 → Estado: Pendiente

---

## Preguntas frecuentes

**¿Puedo modificar un pago después?**
> Sí, pero si cambiás las CxP vinculadas, el sistema no re-procesa automáticamente. Contactá al administrador del sistema.

**¿Qué pasa si el pago es mayor que la deuda total?**
> El sistema asigna solo lo necesario. El excedente no se asigna.

**¿Puedo ver el historial de pagos de una factura?**
> Sí, en "Cuentas por Pagar", cada factura tiene un campo "Asignaciones de Pagos" que muestra todos los pagos que la cubrieron.
