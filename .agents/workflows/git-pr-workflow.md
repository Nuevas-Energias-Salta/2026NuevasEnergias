---
description: Flujo de trabajo estándar de Git para crear Pull Requests en este repositorio.
---
// turbo-all

Este flujo asegura que todos los cambios se integren correctamente siguiendo la política de Pull Requests del proyecto.

1. **Sincronizar con el repositorio remoto**:
   Asegúrate de estar en `main` y tener lo último.
   `git checkout main`
   `git pull origin main`

2. **Crear una rama nueva**:
   Usa un nombre descriptivo (ej: `feat/calculadora-cxc` o `fix/error-notion`).
   `git checkout -b [nombre-de-la-rama]`

3. **Realizar cambios y confirmar**:
   Haz los cambios necesarios en el código.
   `git add .`
   `git commit -m "[Mensaje descriptivo en español]"`

4. **Subir la rama**:
   `git push origin [nombre-de-la-rama]`

5. **Crear Pull Request**:
   Utiliza la herramienta `create_pull_request` del servidor MCP de GitHub para abrir el PR hacia la rama `main`.
