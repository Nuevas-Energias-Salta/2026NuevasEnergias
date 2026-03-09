# Resumen Final: Sistema de Gestión de Informes FV 🚀
## Nuevas Energías Salta

Este documento detalla el funcionamiento completo del sistema de automatización de informes de ahorro energético, diseñado para procesar datos de generación (Growatt) y consumo (EDESA) de forma mensual y automática.

---

## 🏗️ Arquitectura del Sistema

El sistema utiliza una aplicación centralizada (`app_gestion_total.py`) con una interfaz gráfica (GUI) que orquesta las 5 fases principales del proceso:

### 🏁 Fase 0: Verificación de Tarifas
- **Qué hace**: Asegura que los cálculos de ahorro se realicen con los precios actuales de la energía.
- **Cómo lo hace**: El usuario debe verificar manualmente los valores en `tarifa_edesa.py`. Existe una herramienta en la app para descargar el último PDF oficial de EDESA y compararlo.

### ☀️ Fase 1: Extracción de Growatt
- **Qué hace**: Obtiene los datos de generación solar de cada cliente directamente desde el portal de Growatt.
- **Cómo lo hace**: Utiliza un script que simula la navegación (o accede a APIs) para descargar los kWh generados del mes y actualiza automáticamente la planilla de Google Sheets.

### 📄 Fase 2: Procesamiento de EDESA
- **Qué hace**: Descarga las facturas de todos los clientes y extrae los datos de consumo de la red.
- **Cómo lo hace**: 
  1. Conéctase a la oficina virtual de EDESA mediante el NIS.
  2. Descarga el PDF y lo sube a una carpeta específica en Google Drive.
  3. Procesa el texto del PDF para extraer: Consumo Punta, Valle, Resto y Energía Inyectada.
  4. Envía estos datos a la planilla maestra de Google Sheets.

### 📊 Fase 3: Generación de Informes
- **Qué hace**: Crea informes interactivos en HTML para cada cliente.
- **Cómo lo hace**: `generar_informes.py` lee los datos consolidados de Google Sheets, calcula métricas (ahorro $, CO₂ evitado, consumo vs generación) y genera archivos HTML con gráficos dinámicos (usando Chart.js).

### ☁️ Fase 4: Publicación y Envío
- **Qué hace**: Publica los informes en internet y notifica a los clientes.
- **Cómo lo hace**:
  1. Los archivos HTML se suben automáticamente a un repositorio de **GitHub Pages**. cada cliente tiene su propia URL privada: `https://.../informes-fv/[nombre-cliente]/`
  2. (Opcional) La Fase 4 de la app envía un email al cliente con el link directo a su informe actual.

---

## 📂 Mapa de Archivos Principales

| Archivo | Función |
| :--- | :--- |
| **`app_gestion_total.py`** | El corazón del sistema (App de Windows). |
| `generar_informes.py` | Genera los informes HTML y los sube a GitHub. |
| `tarifa_edesa.py` | Contiene los valores de las tarifas que deben actualizarse. |
| `nis_nombres.py` | Mapeo entre números de NIS y nombres de clientes. |
| `email_sender.py` | Lógica para el envío de correos automáticos. |
| `extractor_zzz.py` | Funciones para leer/escribir en Google Sheets. |

---

## 🛠️ Guía de Mantenimiento Mensual

Para dar por terminado el proyecto y asegurar su correcta operación futura, sigue estos pasos cada mes:

1. **Abrir `tarifa_edesa.py`**: Actualizar los valores de los cargos variables según el nuevo cuadro tarifario.
2. **Ejecutar `python app_gestion_total.py`**.
3. **Seleccionar el periodo** (ej: "mar 2026").
4. **Marcar todas las fases** (Fase 1, 2 y 3 son esenciales).
5. **Clic en "INICIAR PROCESO COMPLETO"**.
6. **Verificar**: Al finalizar, revisa que los informes en GitHub Pages se hayan actualizado con la nueva fecha.

---

> [!IMPORTANT]
> El sistema está diseñado para ser resiliente. Si un cliente falla (por ejemplo, por un NIS incorrecto), el proceso continuará con el siguiente y emitirá un log de error al final para su revisión manual.

**¡Proyecto Completado!** Con este manual, el sistema es totalmente autónomo para la gestión mensual de Nuevas Energías Salta.
