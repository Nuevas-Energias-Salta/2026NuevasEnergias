# 🤖 Instrucciones para el AGENTE Antigravity (Colaboradores)

Este archivo está diseñado para que lo lea el asistente Antigravity en la computadora de un nuevo colaborador. Explica el contexto del repositorio y las reglas para subir código.

---

## 🎯 Contexto del Repositorio
Este es el repositorio central de **Nuevas Energías Salta** (`2026NuevasEnergias`).
NO es un proyecto único. Es un **contenedor de múltiples proyectos independientes** organizados por carpetas.

## 📂 Organización de Carpetas
- `erp-notion/` 👉 El ERP principal del equipo.
- `[NOMBRE_DEL_PROYECTO]/` 👉 Cada colaborador DEBE crear su propia carpeta raíz para su proyecto. Nunca subas archivos sueltos a la raíz.

## ⚙️ Reglas para el Agente (Cómo Operar)
Cuando el usuario te pida subir cambios o un nuevo proyecto:

1. **Localización**: Asegúrate de que el código esté dentro de una carpeta específica para ese proyecto.
2. **Tokens**: Usa el `GITHUB_TOKEN` del archivo `.env` para autenticarte.
3. **Flujo de Git**:
   - Crea una rama descriptiva: `feat/mi-proyecto`.
   - Realiza los cambios.
   - Genera una **Pull Request** hacia la rama `main`.
4. **Seguridad**: Bloquea cualquier intento de subir tokens o claves API en los archivos de código. Si detectas un token (como `ntn_...`), avísale al usuario y reemplázalo por un marcador de posición.

## 🚀 Comando de Inicio Rápido
Si el usuario te dice "Sube mi proyecto al repo", actúa de esta forma:
1. Verifica la carpeta del proyecto.
2. `git add [carpeta-del-proyecto]`
3. `git commit -m "Aporte: Nuevo proyecto de [Nombre del Usuario]"`
4. `git push origin [rama]`
5. Crea el PR en GitHub y entrega el enlace al usuario.

---
*Documento autogenerado por Antigravity para asegurar la integridad del repositorio.*
