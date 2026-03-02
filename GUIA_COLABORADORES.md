# Guía General para Colaboradores ☀️

Bienvenido al equipo de desarrollo de **Nuevas Energías Salta**. Esta guía explica cómo colaborar en los distintos proyectos de la empresa utilizando Git y nuestro asistente de IA, **Antigravity**.

---

## 🚀 Cómo Subir Cambios (Pull Requests)

Para mantener la seguridad de nuestros códigos y proyectos, usamos un flujo de **Pull Requests (PR)**. Esto significa que los cambios se proponen en una "rama" aparte y se revisan antes de unirse al proyecto principal.

### 1. Pedir a Antigravity que realice el trabajo
Si estás usando Antigravity, no necesitas escribir comandos de Git. Simplemente dile qué quieres hacer:
> *"Agente, crea una nueva rama llamada 'mejora-reportes' y sube estos cambios mediante una Pull Request."*

### 2. Flujo de Trabajo Interno (Lo que hace la IA por ti)
Antigravity seguirá estos pasos automáticamente:
1.  **Crear una rama nueva**: Por ejemplo, `feature/nueva-funcionalidad`.
2.  **Hacer el Commit**: Guardar los cambios con un mensaje explicativo.
3.  **Push**: Subir los cambios a GitHub.
4.  **Generar la Pull Request**: Crear la solicitud de revisión en GitHub.

### 3. Revisión y Mezcla (Merge)
Una vez creada la Pull Request, un responsable del equipo revisará los cambios. Si todo está correcto, se aceptará la solicitud y los cambios pasarán a formar parte del repositorio principal en la rama `main`.

---

## 📦 Estructura de Proyectos

Al subir un nuevo proyecto o script, por favor asegúrate de colocarlo en la carpeta correspondiente para mantener el repositorio organizado:
-   Si es algo del ERP: `/erp`
-   Si es una automatización: `/automatizaciones`
-   Si es documentación general: `/docs`

---

## ⚠️ Reglas Importantes
-   **NUNCA subir contraseñas o tokens**: Usa archivos `.env` (que no se suben) para las claves privadas.
-   **NUNCA subir directamente a `main`**: Siempre usa el flujo de Pull Requests para que tu trabajo pueda ser revisado y validado.
-   **En Español**: Toda la documentación y mensajes de commit deben ser en español.

---
*¡Gracias por contribuir al crecimiento tecnológico de Nuevas Energías Salta!*
