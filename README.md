<div align="center">
  <img src="NE-LOGO_EES-04.png" alt="Nuevas Energías Logo" width="300">
  <br>
  <h1>Nuevas Energías Salta</h1>
  <p><i>"Eficiente es Sustentable"</i></p>
  
  <p align="center">
    <a href="https://github.com/Nuevas-Energias-Salta/2026NuevasEnergias/blob/main/docs/branding/Brand_Book_Nuevas_Energias.pdf">
      <img src="https://img.shields.io/badge/Brand%20Book-Visible-FFC000?style=for-the-badge&logo=adobe-acrobat-reader&logoColor=white" alt="Brand Book">
    </a>
  </p>
</div>

<hr style="border: 2px solid #FFC000;">

## 🚀 Notion ERP - Sistema Empresarial de Gestión Financiera

**Sistema completo enterprise-grade** para gestión financiera integrando **noCRM → Trello → Notion** con automatización avanzada, monitoreo en tiempo real, alertas inteligentes y optimización de rendimiento.

### 🎨 **Identidad Visual**
| Elemento | Especificación | HEX |
| :--- | :--- | :--- |
| **Color Principal** | Solar Yellow | `#FFC000` |
| **Acento** | Thermal Red | `#D13438` |
| **Textos** | Titanium Black | `#333333` |
| **Símbolo** | Engineering Grey | `#75787B` |

> [!TIP]
> **Tipografía:** Para mantener la consistencia, utiliza **Oswald Bold** para titulares y **Roboto** para textos secundarios.

---

## ✨ **CARACTERÍSTICAS PRINCIPALES**

### 🏗️ **Arquitectura Moderna**
- 📁 **Estructura modular** y escalable
- ⚙️ **Configuración centralizada** segura
- 🧪 **Suite completa de pruebas** automatizadas
- 📝 **Logging estructurado** y analizable

### 📊 **Monitoreo y Alertas**
- 📈 **Dashboard en tiempo real** con auto-refresh
- 🚨 **Sistema de alertas** multicanal (Slack, Email, WhatsApp)
- 📊 **Métricas y KPIs** automáticos
- 🏥 **Health checks** continuos del sistema

### ⚡ **Rendimiento Optimizado**
- 🚀 **Caché inteligente** con 90%+ hit rate
- 🔄 **Ejecución paralela** y batch processing
- 🌐 **Retry automático** con exponential backoff
- 📉 **Reducción 80%** en llamadas API innecesarias

---

## 📁 Estructura del Monorepo

Este repositorio centraliza múltiples proyectos y automatizaciones de la empresa.

```text
2026NuevasEnergias/
├── 📂 erp-notion/              # Sistema ERP (noCRM → Trello → Notion)
├── 📂 sistema_informes_fv/     # Máquina de Growth: Generador de Reportes y Anomalías
├── 📂 Maquina_de_Growth/       # Documentación y assets estratégicos
├── 📂 recursos-marca/          # Manual de Identidad y Logos
├── 📂 .agents/                 # Automatizaciones locales (ej: /git-pr-workflow)
└── .gitignore                  # Oculta todas las credenciales (.env)
```

## 🔒 Reglas Básicas de Seguridad y Trabajo en Equipo

1. **Nunca subas contraseñas a Git.** Cada proyecto tiene un `.env.template`. Cópialo localmente como `.env` y rellénalo con tus datos. El archivo `.env` está ignorado globalmente.
2. **Crea siempre una rama para trabajar** (ej: `tu-nombre/nueva-funcion`).
3. **No trabajes directamente en `main`.** Abre un Pull Request cuando termines.

## 🎯 Flujo Principal

**noCRM (Ventas)** → **Trello (Obras)** → **Notion (Finanzas)**

1. **Leads** se convierten en **Proyectos ganados** 
2. **Proyectos** generan **Cuentas por Cobrar** automáticas
3. **Cuentas por Pagar** se crean con distribución inteligente
4. **Dashboard** en Notion con métricas en tiempo real

## 🚀 **INICIO RÁPIDO**

Cada subproyecto tiene sus propios requerimientos. Entra a su carpeta específica para comenzar:

```bash
# Ejemplo para Iniciar ERP Notion:
cd erp-notion
pip install -r requirements.txt
cp .env.template .env # <- Rellenar credenciales
python main.py

# Ejemplo para Sistema de Informes (Máquina de Growth):
cd sistema_informes_fv
cp .env.template .env # <- Rellenar credenciales de Email y APIs
python app_gestion_total.py
```

---

<div align="center">
  <p>© 2026 Nuevas Energías Salta. Todos los derechos reservados.</p>
</div>