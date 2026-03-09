# Solución al problema de descarga automática en GitHub Pages

## Problema identificado
Cuando accedes a tu sitio de GitHub Pages, el navegador descarga el archivo HTML en lugar de mostrarlo.

## Causas posibles y soluciones

### 1. **Problema más común: Caché del navegador**

El navegador tiene cacheada una versión antigua del archivo que tenía headers incorrectos.

**SOLUCIÓN:**
- Presiona `Ctrl + Shift + R` (Windows/Linux) o `Cmd + Shift + R` (Mac) para hacer un hard refresh
- O abre el sitio en modo incógnito: `Ctrl + Shift + N`

### 2. **Verificar que el archivo se subió correctamente**

**Pasos:**
1. Ve a tu repositorio en GitHub: https://github.com/administracion-ne/informes-fv
2. Navega a la carpeta del cliente (ejemplo: `/cendis/`)
3. Verifica que existe un archivo `index.html` (NO `index` sin extensión)
4. Haz clic en el archivo y verifica que comience con `<!DOCTYPE html>`

### 3. **Verificar GitHub Pages**

1. Ve a Settings → Pages en tu repositorio
2. Verifica que está configurado para usar la rama `main` y carpeta raíz `/`
3. Espera 1-2 minutos después de hacer push para que GitHub actualice

### 4. **Verificación del código HTML**

El archivo generado NO debe tener:
- Líneas en blanco antes de `<!DOCTYPE html>`
- Caracteres BOM al inicio
- Headers de Python/Flask accidentales

**Verificación:** Abre el archivo "download (4)" que tienes en tu carpeta y confirma que la primera línea sea exactamente:
```html
<!DOCTYPE html>
```

### 5. **Forzar actualización de GitHub Pages**

Si nada funciona, puedes forzar a GitHub a reconstruir el sitio:

**Opción A: Hacer un cambio dummy**
```bash
cd "C:\Users\Gonza\Desktop\proyecto zzz\github_pages"
echo. >> .nojekyll
git add .
git commit -m "Force rebuild"
git push origin main
```

**Opción B: Deshabilitar y re-habilitar GitHub Pages**
1. Ve a Settings → Pages
2. Cambia Source a "None"
3. Guarda
4. Vuelve a configurarlo en "main" / "root"
5. Espera 2-3 minutos

---

## Prueba rápida: ¿El HTML es correcto?

Para verificar que el HTML generado es correcto:

1. Abre el archivo "download (4)" con un navegador web directamente
   - Haz clic derecho → Abrir con → Chrome/Firefox
   
2. Si se muestra correctamente en local pero no en GitHub Pages, el problema es de GitHub/caché

3. Si tampoco se muestra en local, el problema está en el HTML generado

---

## Solución inmediata recomendada:

1. **PASO 1:** Abre el sitio en modo incógnito:
   - Chrome: `Ctrl + Shift + N`
   - URL: https://administracion-ne.github.io/informes-fv/cendis/

2. **PASO 2:** Si aún descarga, espera 5 minutos (GitHub Pages tarda en actualizar)

3. **PASO 3:** Si persiste, verifica en GitHub que el archivo `index.html` existe y tiene el contenido correcto

4. **PASO 4:** Como último recurso, ejecuta el script de forzar rebuild arriba

---

## Nota importante:

El contenido del archivo "download (4)" que tienes es **CORRECTO**. Comienza con `<!DOCTYPE html>` y tiene toda la estructura válida. Esto significa que el problema es muy probablemente caché o que GitHub Pages no se ha actualizado aún.

**RECOMENDACIÓN FINAL:**
1. Abre en incógnito
2. Si no funciona, espera 5-10 minutos y vuelve a intentar
3. Si persiste después de 10 minutos, ejecuta el "Force rebuild" de arriba
