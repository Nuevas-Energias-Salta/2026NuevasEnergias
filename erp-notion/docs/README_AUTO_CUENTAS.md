# Generación Automática de Cuentas - Guía

## 📋 Scripts Disponibles

### 1. `auto_generate_cxc_improved.py`
Genera **Cuentas por Cobrar** automáticamente desde los proyectos.

**Características:**
- ✅ Verificación de duplicados
- ✅ Dos modos: pago único o pagos parciales (anticipo/cuotas/saldo)
- ✅ Vinculación automática con cliente y proyecto
- ✅ Estados automáticos según estado del proyecto

**Configuración (en el código):**
```python
CONFIG = {
    "generar_cuotas": True,          # True = pagos parciales, False = pago único
    "anticipo_porcentaje": 0.30,     # 30% anticipo
    "numero_cuotas": 2,              # 2 cuotas intermedias
    "saldo_final_porcentaje": 0.20,  # 20% saldo final
    "dias_entre_cuotas": 30,
    "dias_vencimiento_anticipo": 7,
    "dias_vencimiento_cuota": 15,
    "dias_vencimiento_saldo": 30
}
```

**Uso:**
```bash
python auto_generate_cxc_improved.py
```

---

### 2. `auto_generate_cxp.py`
Genera **Cuentas por Pagar** automáticamente desde los proyectos.

**Características:**
- ✅ Genera gastos estimados por categorías
- ✅ Asignación automática de proveedores según categoría
- ✅ Verificación de duplicados
- ✅ Múltiples cuentas por proyecto

**Distribución de gastos (en el código):**
```python
GASTOS_CONFIG = [
    {"categoria": "Materiales", "porcentaje": 0.55},     # 55%
    {"categoria": "Materiales", "porcentaje": 0.15},     # 15% (segunda compra)
    {"categoria": "Mano de Obra", "porcentaje": 0.20},   # 20%
    {"categoria": "Transporte", "porcentaje": 0.05},     # 5%
    {"categoria": "Otros", "porcentaje": 0.05},          # 5%
]
```

**Uso:**
```bash
python auto_generate_cxp.py
```

---

### 3. `auto_generate_accounts.py` ⭐ RECOMENDADO
Script unificado que ejecuta ambos procesos con un menú interactivo.

**Características:**
- ✅ Menú interactivo para elegir qué generar
- ✅ Configuración guiada
- ✅ Puede ejecutar CxC, CxP o ambos

**Uso:**
```bash
python auto_generate_accounts.py
```

**Opciones del menú:**
1. Generar solo CxC
2. Generar solo CxP
3. Generar ambas
4. Salir

---

## 🎯 Casos de Uso

### Caso 1: Proyectos nuevos importados de Trello
Si acabas de importar proyectos desde Trello, ejecuta:
```bash
python auto_generate_accounts.py
```
Elige opción 3 para generar tanto CxC como CxP.

### Caso 2: Solo necesitas facturación a clientes
```bash
python auto_generate_cxc_improved.py
```

### Caso 3: Solo necesitas gestionar pagos a proveedores
```bash
python auto_generate_cxp.py
```

---

## ⚙️ Personalización

### Ajustar porcentajes de CxC
Edita `auto_generate_cxc_improved.py` líneas 28-36 para cambiar:
- Porcentaje de anticipo
- Número de cuotas
- Días de vencimiento

### Ajustar categorías de CxP
Edita `auto_generate_cxp.py` líneas 28-34 para:
- Agregar/quitar categorías
- Cambiar porcentajes
- Modificar plazos de pago

---

## 🔍 Verificación

Después de ejecutar los scripts:

1. **En Notion → Cuentas por Cobrar:**
   - Verifica que cada proyecto tenga sus cuentas
   - Revisa que los montos sean correctos
   - Confirma las fechas de vencimiento

2. **En Notion → Cuentas por Pagar:**
   - Verifica las categorías asignadas
   - Confirma que los proveedores estén vinculados
   - Revisa los estados

3. **En Notion → Proyectos:**
   - Abre un proyecto
   - Verifica que las relaciones con CxC y CxP funcionen

---

## ⚠️ Importante

- Los scripts **NO crean duplicados**: verifican si ya existen cuentas para cada proyecto
- Los estados se asignan automáticamente según el estado del proyecto
- Si un proyecto está "Cancelado", NO se generan cuentas
- Si un proyecto está "Finalizado", las cuentas se marcan como "Cobrado"/"Pagado"

---

## 🐛 Solución de Problemas

**Error: "Sin cliente"**
→ El proyecto no tiene cliente asignado. Asigna un cliente en Notion.

**Error: "Sin monto"**
→ El proyecto no tiene monto o es 0. Completa el campo "Monto Contrato".

**"Ya tiene X cuenta(s)"**
→ No es un error, simplemente el proyecto ya tiene cuentas generadas.

---

## 📝 Notas

- Puedes ejecutar los scripts múltiples veces de forma segura
- Los scripts respetan los datos existentes
- Siempre revisa los resultados en Notion antes de usar los datos para facturación real
