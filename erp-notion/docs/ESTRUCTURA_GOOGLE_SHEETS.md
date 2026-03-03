# 📊 ESTRUCTURA GOOGLE SHEETS PARA LOOKER STUDIO

## Hojas del Spreadsheet

Crear un Google Sheet llamado "Nuevas Energías - Dashboard" con las siguientes hojas:

---

## HOJA 1: Proyectos

| Columna | Tipo | Descripción |
|---------|------|-------------|
| ID | Texto | ID del proyecto en Notion |
| Nombre | Texto | Nombre del proyecto |
| Cliente | Texto | Nombre del cliente |
| Estado | Texto | Cotización/Aprobado/En Ejecución/Finalizado/Cancelado |
| Centro_Costo | Texto | Solar/Climatización/ACS/etc |
| Monto_Contrato | Número | Valor del contrato |
| Fecha_Inicio | Fecha | Fecha de inicio |
| Fecha_Fin | Fecha | Fecha estimada de fin |
| Fecha_Creacion | Fecha | Cuándo se creó el registro |

---

## HOJA 2: CxC (Cuentas por Cobrar)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| ID | Texto | ID de la CxC en Notion |
| Proyecto | Texto | Nombre del proyecto |
| Cliente | Texto | Nombre del cliente |
| Monto_Total | Número | Monto total a cobrar |
| Monto_Cobrado | Número | Monto ya cobrado |
| Saldo_Pendiente | Número | Lo que falta cobrar |
| Estado | Texto | Pendiente/Parcial/Cobrado/Vencido |
| Fecha_Emision | Fecha | Cuándo se emitió |
| Fecha_Vencimiento | Fecha | Cuándo vence |

---

## HOJA 3: Cobros

| Columna | Tipo | Descripción |
|---------|------|-------------|
| ID | Texto | ID del cobro |
| CxC | Texto | Referencia a la CxC |
| Cliente | Texto | Nombre del cliente |
| Monto | Número | Monto cobrado |
| Fecha | Fecha | Fecha del cobro |
| Metodo_Pago | Texto | Transferencia/Efectivo/Cheque/etc |

---

## HOJA 4: Clientes

| Columna | Tipo | Descripción |
|---------|------|-------------|
| ID | Texto | ID del cliente |
| Nombre | Texto | Nombre completo |
| Email | Texto | Email de contacto |
| Telefono | Texto | Teléfono |
| Total_Proyectos | Número | Cantidad de proyectos |
| Total_Facturado | Número | Total facturado histórico |

---

## HOJA 5: Resumen (Fórmulas)

Esta hoja tendrá métricas calculadas:

| Métrica | Fórmula |
|---------|---------|
| Total Proyectos | =COUNTA(Proyectos!A:A)-1 |
| Total Clientes | =COUNTA(Clientes!A:A)-1 |
| Monto Total CxC | =SUM(CxC!D:D) |
| Monto Cobrado | =SUM(CxC!E:E) |
| Saldo Pendiente | =SUM(CxC!F:F) |
| % Cobrado | =Monto_Cobrado/Monto_Total*100 |

---

## Próximos Pasos

1. Crear el Google Sheet con esta estructura
2. Ejecutar el script de exportación (ver export_to_sheets.py)
3. Importar los CSVs en Google Sheets
4. Configurar Zapier para mantener sincronizado
5. Conectar a Looker Studio
