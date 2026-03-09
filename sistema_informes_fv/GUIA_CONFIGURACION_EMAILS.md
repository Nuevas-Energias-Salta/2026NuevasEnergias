# 📧 Guía de Configuración - Envío Automático de Emails

## Descripción General

Esta guía te ayudará a configurar el sistema de envío automático de emails para los informes mensuales de consumo solar. Los clientes recibirán un email profesional con un enlace directo a su informe interactivo.

---

## 📋 Requisitos Previos

1. ✅ Tener los informes generándose correctamente (Fase 3)
2. ✅ GitHub Pages configurado y funcionando
3. ✅ Una cuenta de email para enviar (Gmail o Outlook)
4. ✅ Los emails de tus clientes

---

## 🔧 Configuración Paso a Paso

### 1️⃣ Instalar Dependencias

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
pip install python-dotenv
```

### 2️⃣ Configurar Credenciales de Email

#### Opción A: Gmail (Recomendado)

1. **Habilitar verificación en 2 pasos** en tu cuenta de Google
   - Ir a: https://myaccount.google.com/security
   - Activar "Verificación en 2 pasos"

2. **Crear contraseña de aplicación**
   - Ir a: https://myaccount.google.com/apppasswords
   - Seleccionar "Correo" y "Windows Computer"
   - Copiar la contraseña generada (16 caracteres)

3. **Crear archivo `.env`** en la carpeta del proyecto:
   ```bash
   # Copiar .env.example como .env
   copy .env.example .env
   ```

4. **Editar `.env`** con tus datos:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USER=tu_email@gmail.com
   EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
   EMAIL_FROM_NAME=Nuevas Energías
   GITHUB_PAGES_BASE=https://administracion-ne.github.io/informes-fv/
   ```

#### Opción B: Outlook/Hotmail

1. **Editar `.env`**:
   ```env
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   EMAIL_USER=tu_email@outlook.com
   EMAIL_PASSWORD=tu_contraseña_normal
   EMAIL_FROM_NAME=Nuevas Energías
   GITHUB_PAGES_BASE=https://administracion-ne.github.io/informes-fv/
   ```

### 3️⃣ Configurar Emails de Clientes

1. **Editar `emails_clientes.json`** con los emails reales:

```json
{
  "_comentario": "Mapeo de NIS a emails de clientes",
  
  "3011513": "cliente.robles@email.com",
  "1234567": "otro.cliente@email.com",
  "7654321": "cliente3@email.com"
}
```

⚠️ **Importante**: 
- Los NIS deben ser exactamente los mismos que aparecen en tus informes
- Usar el formato de string (entre comillas)
- Las líneas que empiezan con `_` son comentarios y se ignoran

### 4️⃣ Verificar URL de GitHub Pages

1. Busca tu URL de GitHub Pages en la configuración de tu repo
2. Actualiza `GITHUB_PAGES_BASE` en el archivo `.env`
3. Formato correcto: `https://usuario.github.io/nombre-repo` (sin `/` al final)

---

## 🧪 Prueba de Configuración

Antes de usar la app completa, prueba el envío de un email individual:

1. **Editar `email_sender.py`** en la función `test_enviar_email()`:
   ```python
   exito, mensaje = enviar_email(
       destinatario="TU_EMAIL@ejemplo.com",  # 👈 CAMBIAR
       nombre_cliente="Cliente de Prueba",
       link_informe="https://ejemplo.com/informe.html",
       periodo="Febrero 2026",
       ...
   ```

2. **Ejecutar prueba**:
   ```powershell
   python email_sender.py
   ```

3. **Verificar resultado**:
   - ✅ Si funciona: Deberías recibir un email en unos segundos
   - ❌ Si falla: Revisar el mensaje de error y las credenciales

---

## 🚀 Uso en la Aplicación

### Envío Automático Completo

1. Abrir `app_gestion_total.py`
2. Seleccionar las fases a ejecutar:
   - ☑️ Fase 1: Growatt
   - ☑️ Fase 2: EDESA  
   - ☑️ Fase 3: Informes
   - ☑️ Fase 4: Emails  👈 **Activar esta casilla**
3. Click en "▶ INICIAR PROCESO COMPLETO"
4. Cuando llegue a Fase 4, aparecerá un diálogo de confirmación
5. Verificar información y confirmar envío

### Envío Manual (Solo Emails)

Si ya tienes los informes generados y solo quieres enviar emails:

1. ☑️ Fase 4: Emails (solo esta)
2. Iniciar proceso
3. Confirmar envío

---

## 📊 Qué Recibirán los Clientes

Los clientes recibirán un email profesional con:

### **Encabezado**
- Logo y branding de Nuevas Energías
- Colores corporativos (amarillo/naranja y rojo)

### **Contenido**
- Saludo personalizado con su nombre
- Periodo del informe
- 3 métricas destacadas:
  - Consumo Total
  - Generación FV
  - Ahorro Estimado

### **Call to Action**
- Botón grande: "📊 Ver Informe Completo"
- Link directo al informe en GitHub Pages

### **Footer**
- Fecha de generación
- Información de contacto

---

## 🔍 Solución de Problemas

### Error: "Credenciales no configuradas"
- ✅ Verificar que existe el archivo `.env` (no `.env.example`)
- ✅ Verificar que `EMAIL_USER` y `EMAIL_PASSWORD` están completos

### Error: "Error de autenticación"
**Gmail:**
- ✅ Usar contraseña de aplicación (no tu contraseña normal)
- ✅ Verificación en 2 pasos debe estar activada

**Outlook:**
- ✅ Intentar con contraseña normal primero
- ✅ Si falla, habilitar "Permitir aplicaciones menos seguras"

### Error: "No se encontró emails_clientes.json"
- ✅ Crear el archivo en la carpeta raíz del proyecto
- ✅ Verificar formato JSON válido

### Email no llega o va a SPAM
- ✅ Verificar que `EMAIL_FROM_NAME` está configurado
- ✅ Pedir a los clientes que agreguen tu email a contactos
- ✅ Considerar usar un dominio profesional en el futuro

### Error: "Sin email configurado" para algunos clientes
- ✅ Verificar que el NIS está en `emails_clientes.json`
- ✅ Verificar que el NIS coincide exactamente (con o sin espacios)

---

## 📈 Mejoras Futuras (Opcional)

### SendGrid (Más Profesional)
Para mejor deliverability y tracking:
1. Crear cuenta en SendGrid (100 emails/día gratis)
2. Obtener API Key
3. Actualizar `email_sender.py` para usar SendGrid API
4. Beneficios:
   - Mejor deliverability (menos SPAM)
   - Tracking de apertura de emails
   - Estadísticas detalladas
   - Mayor límite de envíos

### Dominio Propio
- Configurar email con dominio propio (`info@nuevasenergias.com`)
- Mejora la imagen profesional
- Reduce probabilidad de ir a SPAM

### Templates Personalizados
- Agregar logo como imagen embebida
- Personalizar colores según cliente
- Agregar gráficos en el email

---

## 📝 Checklist de Configuración

Antes de usar en producción, verificar:

- [ ] `.env` creado con todas las credenciales
- [ ] Prueba de email exitosa (`python email_sender.py`)
- [ ] `emails_clientes.json` completo con todos los clientes
- [ ] URL de GitHub Pages correcta en `.env`
- [ ] Email de prueba recibido y visualizado correctamente
- [ ] Informes generandose correctamente (Fase 3)
- [ ] GitHub Pages funcionando y desplegado

---

## 🆘 Soporte

Si encuentras problemas:

1. Revisar logs en la aplicación (consola negra)
2. Verificar archivo `.env` línea por línea
3. Probar con `email_sender.py` standalone
4. Verificar que no hay firewalls bloqueando puerto 587

---

## 🎉 ¡Listo!

Una vez configurado, el proceso completo será:

```
Fase 1: Extraer datos de Growatt → 
Fase 2: Descargar facturas EDESA → 
Fase 3: Generar informes HTML → 
Fase 4: Enviar emails automáticamente → 
✅ ¡Clientes reciben sus informes!
```

**¡100% automatizado!** 🚀
