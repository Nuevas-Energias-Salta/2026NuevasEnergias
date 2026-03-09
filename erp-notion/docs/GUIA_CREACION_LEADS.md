# 📋 Guía de Creación de Leads en noCRM

## ⚠️ REQUISITO OBLIGATORIO

### Formato del Nombre del Lead

```
NOMBRE CLIENTE - DESCRIPCIÓN PROYECTO
```

**Ejemplos correctos:**
- ✅ `Juan Pérez - Instalación Solar 5kW`
- ✅ `María García - Climatización Pileta`
- ✅ `Empresa ABC - Proyecto Biomasa`

**Ejemplos incorrectos:**
- ❌ `Instalación Solar 5kW` (falta nombre cliente)
- ❌ `Juan Pérez` (falta descripción proyecto)
- ❌ `Solar FV Juan` (formato incorrecto)

---

## 📝 Campos Requeridos al Crear Lead

| Campo | Obligatorio | Ejemplo | Notas |
|-------|-------------|---------|-------|
| **Nombre Lead** | ✅ SÍ | `Juan Pérez - Solar FV` | Formato: `CLIENTE - PROYECTO` |
| **Email** | ✅ SÍ | `juan@email.com` | Para contacto |
| **Teléfono/Celular** | ✅ SÍ | `+54 387 123456` | Números únicamente |
| **Monto Total** | ✅ SÍ | `1,500,000` | Sin símbolos de moneda |
| **Tags/Etiquetas** | ✅ SÍ | `Biomasa`, `Solar` | Para Centro de Costo |

---

## 🏷️ Tags/Etiquetas para Centro de Costo

Usar **UNA** de estas etiquetas según el tipo de proyecto:

| Etiqueta | Centro de Costo en Notion |
|----------|---------------------------|
| `Solar`, `FV`, `Fotovoltaico` | Solar Fotovoltaico |
| `Piletas`, `Climatización` | Climatización Piletas |
| `ACS`, `Agua Caliente` | ACS |
| `Biomasa` | Biomasa |
| `Calefacción`, `PRE` | Calefacción Eléctrica |
| `Luminaria` | Luminaria Solar |
| `Consultoría`, `Gestoria` | Varios |

---

## 🔄 Qué Pasa Cuando el Lead se marca como "GANADO"

1. **En Trello**: Se crea tarjeta automáticamente con:
   - Nombre completo del lead
   - Monto en custom field
   - Email y Celular en custom fields
   - Etiqueta según Centro de Costo

2. **En Notion**: Se crea automáticamente:
   - **Cliente** (si no existe): Nombre antes del guión
   - **Proyecto**: Nombre después del guión
   - **Cuenta por Cobrar**: Vinculada al proyecto

---

## ✅ Checklist Antes de Marcar "Ganado"

- [ ] Nombre tiene formato `CLIENTE - PROYECTO`
- [ ] Email está completo
- [ ] Teléfono/Celular está completo
- [ ] Monto total está cargado
- [ ] Al menos una etiqueta de Centro de Costo

---

## ❓ Solución de Problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| Cliente no se crea | Falta guión en nombre | Agregar formato `Nombre - Proyecto` |
| Centro Costo = Varios | Etiqueta no reconocida | Usar etiquetas de la tabla |
| Monto = 0 | Campo vacío | Cargar monto antes de ganar |
