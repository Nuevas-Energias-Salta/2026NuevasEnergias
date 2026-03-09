# 🚀 Guía para Colaboradores: Cómo trabajar con Antigravity

Esta guía explica cómo configurar tu entorno y subir cambios al repositorio **Nuevas Energías Salta** usando nuestro asistente de IA **Antigravity**.

---

## 🔑 Configuración de GitHub (Permisos del Token)

Para que Antigravity pueda subir tus cambios y crear Pull Requests, necesitas generar un **Personal Access Token (PAT)** con los siguientes permisos. 

### Opción 1: Fine-grained Token (Recomendado y más seguro)
1. Ve a [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta).
2. Haz clic en **Generate new token**.
3. En **Repository access**, selecciona **Only select repositories** y elige `Nuevas-Energias-Salta/2026NuevasEnergias`.
4. En **Permissions**, busca **Repository permissions** y otorga:
   - ✅ **Contents**: Read & Write (Necesario para subir código).
   - ✅ **Pull requests**: Read & Write (Necesario para crear PRs).
   - ✅ **Metadata**: Read-only (Se selecciona automáticamente).
5. Genera el token y guárdalo en tu archivo `.env`.

### Opción 2: Classic Token (Más simple)
1. Ve a [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens).
2. Selecciona el scope:
   - ✅ **repo** (Full control of private repositories).
3. Genera el token y guárdalo en tu archivo `.env`.

---

## 🛠️ Configuración Inicial del Proyecto

1. **Clonar el Repositorio**:
   `git clone https://github.com/Nuevas-Energias-Salta/2026NuevasEnergias.git`
2. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configurar Variables de Entorno**:
   - Crea un archivo `.env` basado en `.env.example`.
   - Agrega tu `GITHUB_TOKEN` recién generado.
   - Agrega tus tokens de Notion y Trello según corresponda.

---

## 📤 Cómo subir cambios (Flujo de Pull Requests)

No subimos cambios directamente a `main`. Usamos ramas y Pull Requests para que **Gonza** (Admin) pueda revisarlos.

### Uso de Antigravity para automatizar:
Simplemente abre el chat con Antigravity y dile:
> *"Agente, crea una rama llamada 'mi-mejora' con mis cambios actuales y genera una Pull Request."*

Antigravity se encargará de:
1. Crear la rama localmente.
2. Hacer el commit con tus cambios.
3. Subir la rama a GitHub.
4. Crear la Pull Request en GitHub y darte el enlace.

---

## 🚫 Nota importante sobre Docker
**NO es necesario instalar Docker.** El proyecto está diseñado para ejecutarse directamente con Python en Windows/Linux. Puedes ignorar cualquier mensaje del editor sugiriendo contenedores.

## 🤖 Para tu Agente Antigravity
Si tu asistente no sabe qué hacer, dile que lea el archivo `INSTRUCCIONES_AGENTE.md` que está en la raíz. Ahí tiene todas las reglas para configurar la conexión y subir todo correctamente.

---

¡Listo! Con esto ya puedes colaborar de forma segura y eficiente. 🚀
