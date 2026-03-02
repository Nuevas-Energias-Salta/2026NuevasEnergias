# 🚀 Guía para Colaboradores: Cómo subir cambios con Antigravity

Esta guía explica cómo trabajar en el proyecto **Notion ERP** y subir cambios a GitHub de la manera más sencilla posible, usando nuestro asistente de IA **Antigravity**.

---

## 🚫 IMPORTANTE: Olvídate de Docker
**NO es necesario instalar Docker.** No importa si ves mensajes o sugerencias en tu editor; este proyecto corre directamente con Python.

---

## 🛠️ Configuración Inicial (Una sola vez)

1. **Obtener el Código**: Clona el repositorio desde GitHub:
   `https://github.com/Nuevas-Energias-Salta/2026NuevasEnergias.git`
2. **Instalar Python**: Asegúrate de tener Python 3.x instalado.
3. **Instalar Dependencias**: Abre una terminal en la carpeta del proyecto y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configurar Tokens**: 
   - Copia el archivo `.env.example` y cámbiale el nombre a `.env`.
   - Edita el `.env` con tus propios tokens de Notion y Trello.

---

## 📤 Cómo subir tus cambios con Antigravity (Pull Requests)

Para mantener el código seguro y organizado, usaremos el flujo de **Pull Requests (PR)**. Esto significa que tus cambios no irán directo a `main`, sino que serán revisados primero.

### Pasos a seguir:

1. **Haz tus cambios**: Edita los archivos o crea nuevos según lo necesites.
2. **Pídele la Pull Request**: Abre el chat con Antigravity y dile algo como:
   > *"Agente, crea una nueva rama llamada 'ajuste-calculadora' con mis cambios actuales y genera una Pull Request hacia main."*
3. **Revisión**: Antigravity utilizará el flujo de trabajo preconfigurado en `.agents/workflows/git-pr-workflow.md`, subirá los archivos a una nueva rama y generará el enlace a la Pull Request en GitHub para que **Gonza** pueda revisarla y aprobarla.

### Ejemplos de lo que puedes pedirle:
- *"Agente, sube este nuevo archivo en una rama nueva y crea un PR."*
- *"Agente, sincroniza mi código y prepárame una Pull Request con las mejoras que hice."*

---

## 🔑 Permisos
Antes de intentar subir cambios, asegúrate de que **Gonza** te ha añadido como colaborador en el repositorio de GitHub. Si no tienes permisos, la subida fallará.

---

¡Eso es todo! Con Antigravity, subir código es tan fácil como enviar un mensaje de chat. 🚀
