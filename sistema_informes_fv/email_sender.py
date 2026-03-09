# -*- coding: utf-8 -*-
"""
Sistema de Envío de Emails - Informes ZZZ
==========================================
Envía automáticamente los informes mensuales a los clientes
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Cargar configuración
load_dotenv()

# Configuración de email
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Nuevas Energías')

# Base URL de GitHub Pages
GITHUB_PAGES_BASE = os.getenv('GITHUB_PAGES_BASE', 'https://tu-usuario.github.io/repo')

def crear_template_email(nombre_cliente, link_informe, periodo, metricas=None):
    """
    Crea el HTML del email con el template profesional.
    
    Args:
        nombre_cliente: Nombre del cliente
        link_informe: URL del informe en GitHub Pages
        periodo: Periodo del informe (ej: "Enero 2026")
        metricas: Dict opcional con métricas destacadas
    """
    
    # Valores por defecto para métricas
    if metricas:
        consumo_total = f"{metricas.get('consumo_total', 0):.0f} kWh"
        generacion = f"{metricas.get('generacion', 0):.0f} kWh"
        ahorro = f"${metricas.get('ahorro_estimado', 0):,.0f}"
    else:
        consumo_total = "Ver informe"
        generacion = "Ver informe"
        ahorro = "Ver informe"
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe Mensual - {periodo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <!-- Container principal -->
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header con logo y colores de marca -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #FCC224 0%, #E02E3A 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold;">
                                ☀️ Nuevas Energías
                            </h1>
                            <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px;">
                                Informe Mensual de Consumo
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Saludo personalizado -->
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="color: #333333; margin: 0 0 15px 0; font-size: 22px;">
                                Hola {nombre_cliente},
                            </h2>
                            <p style="color: #666666; margin: 0 0 20px 0; line-height: 1.6; font-size: 16px;">
                                Ya está disponible tu informe de consumo y generación solar correspondiente al periodo de <strong>{periodo}</strong>.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Métricas destacadas -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="33%" style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
                                        <div style="color: #E02E3A; font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                                            {consumo_total}
                                        </div>
                                        <div style="color: #748283; font-size: 12px; text-transform: uppercase;">
                                            Consumo Total
                                        </div>
                                    </td>
                                    <td width="10"></td>
                                    <td width="33%" style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
                                        <div style="color: #FCC224; font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                                            {generacion}
                                        </div>
                                        <div style="color: #748283; font-size: 12px; text-transform: uppercase;">
                                            Generación FV
                                        </div>
                                    </td>
                                    <td width="10"></td>
                                    <td width="33%" style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
                                        <div style="color: #28a745; font-size: 24px; font-weight: bold; margin-bottom: 5px;">
                                            {ahorro}
                                        </div>
                                        <div style="color: #748283; font-size: 12px; text-transform: uppercase;">
                                            Ahorro Estimado
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Call to Action -->
                    <tr>
                        <td style="padding: 20px 30px 30px 30px; text-align: center;">
                            <a href="{link_informe}" 
                               style="display: inline-block; 
                                      background: linear-gradient(135deg, #FCC224 0%, #E02E3A 100%); 
                                      color: #ffffff; 
                                      text-decoration: none; 
                                      padding: 15px 40px; 
                                      border-radius: 25px; 
                                      font-size: 18px; 
                                      font-weight: bold;
                                      box-shadow: 0 4px 15px rgba(224, 46, 58, 0.3);">
                                📊 Ver Informe Completo
                            </a>
                            <p style="color: #999999; margin: 15px 0 0 0; font-size: 13px;">
                                También puedes copiar este enlace:<br>
                                <a href="{link_informe}" style="color: #E02E3A; word-break: break-all;">
                                    {link_informe}
                                </a>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Información adicional -->
                    <tr>
                        <td style="padding: 20px 30px; background-color: #f8f9fa; border-radius: 0 0 10px 10px;">
                            <p style="color: #666666; margin: 0; font-size: 14px; line-height: 1.6;">
                                💡 <strong>Tip:</strong> En el informe encontrarás gráficos interactivos, comparaciones con meses anteriores, 
                                y recomendaciones personalizadas para optimizar tu consumo.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; text-align: center;">
                            <p style="color: #999999; margin: 0; font-size: 12px;">
                                Este informe fue generado automáticamente el {datetime.now().strftime('%d/%m/%Y')}<br>
                                <strong>Nuevas Energías</strong> - Energía Solar para un futuro sostenible
                            </p>
                            <p style="color: #cccccc; margin: 10px 0 0 0; font-size: 11px;">
                                Si tienes dudas o consultas, responde a este email
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    return html


def enviar_email(destinatario, nombre_cliente, link_informe, periodo, metricas=None, callback_log=None):
    """
    Envía un email con el informe al cliente.
    
    Args:
        destinatario: Email del destinatario
        nombre_cliente: Nombre del cliente
        link_informe: URL del informe
        periodo: Periodo del informe
        metricas: Dict opcional con métricas
        callback_log: Función para logging
        
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    
    def log(msg):
        if callback_log:
            callback_log(msg)
    
    # Validar configuración
    if not EMAIL_USER or not EMAIL_PASSWORD:
        return False, "❌ Credenciales de email no configuradas. Revisar archivo .env"
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_USER}>"
        msg['To'] = destinatario
        msg['Subject'] = f"☀️ Tu Informe de Consumo Solar - {periodo}"
        
        # Versión texto plano (fallback)
        texto_plano = f"""
Hola {nombre_cliente},

Ya está disponible tu informe de consumo y generación solar correspondiente al periodo de {periodo}.

Ver informe completo:
{link_informe}

Saludos,
Nuevas Energías
"""
        
        # Agregar contenido
        parte_texto = MIMEText(texto_plano, 'plain', 'utf-8')
        parte_html = MIMEText(crear_template_email(nombre_cliente, link_informe, periodo, metricas), 'html', 'utf-8')
        
        msg.attach(parte_texto)
        msg.attach(parte_html)
        
        # Conectar y enviar
        log(f"    🔌 Conectando a {SMTP_SERVER}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        log(f"    🔐 Autenticando...")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        log(f"    📤 Enviando a {destinatario}...")
        server.send_message(msg)
        server.quit()
        
        log(f"    ✅ Email enviado exitosamente")
        return True, "Email enviado"
        
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Error de autenticación. Verifica EMAIL_USER y EMAIL_PASSWORD"
    except smtplib.SMTPException as e:
        return False, f"❌ Error SMTP: {str(e)}"
    except Exception as e:
        return False, f"❌ Error inesperado: {str(e)}"


def cargar_emails_master():
    """Carga el mapeo de NIS -> Email desde Master_Clientes."""
    emails = {}
    try:
        from nis_nombres import cargar_datos_master, MASTER_CLIENTES_DATA
        cargar_datos_master()
        
        if not MASTER_CLIENTES_DATA:
            return emails
            
        rows = MASTER_CLIENTES_DATA[1:]
        # Índices: 0: NIS, 3: Email_Contacto
        for row in rows:
            if len(row) >= 4:
                nis = str(row[0]).strip()
                email = str(row[3]).strip()
                if nis and email and "@" in email:
                    emails[nis] = email
        
        print(f"✅ Cargados {len(emails)} emails desde Master_Clientes.")
    except Exception as e:
        print(f"⚠️ Error cargando emails: {e}")
    return emails

def enviar_emails_batch(informes, emails_clientes=None, callback_log=None):
    """
    Envía emails a múltiples clientes.
    Si emails_clientes es None, los carga desde Google Sheets.
    """
    
    def log(msg):
        if callback_log:
            callback_log(msg)
    
    if emails_clientes is None:
        log("🔍 Cargando destinatarios desde Google Sheets...")
        emails_clientes = cargar_emails_master()
    
    resultado = {
        'exitosos': 0,
        'fallidos': 0,
        'detalles': []
    }
    
    for informe in informes:
        nis = informe['nis']
        cliente = informe['cliente']
        periodo = informe['periodo']
        
        # Buscar email del cliente
        email_cliente = emails_clientes.get(nis)
        
        if not email_cliente:
            log(f"  ⚠️ {cliente}: Sin email configurado")
            resultado['fallidos'] += 1
            resultado['detalles'].append({
                'cliente': cliente,
                'nis': nis,
                'exito': False,
                'error': 'Email no configurado'
            })
            continue
        
        # Construir URL del informe (basado en la estructura de generar_informes.py)
        # generar_informes.py usa: GITHUB_BASE_URL + sanitizar_url(cliente) + "/"
        from generar_informes import sanitizar_url
        cliente_url = sanitizar_url(cliente)
        
        # Asegurar que la base tiene / al final
        base_url = GITHUB_PAGES_BASE if GITHUB_PAGES_BASE.endswith('/') else GITHUB_PAGES_BASE + '/'
        link_informe = f"{base_url}{cliente_url}/"
        
        log(f"  📧 Enviando a {cliente} ({email_cliente})...")
        
        # Enviar email
        exito, mensaje = enviar_email(
            destinatario=email_cliente,
            nombre_cliente=cliente,
            link_informe=link_informe,
            periodo=periodo,
            metricas=informe.get('metricas'),  # Opcional
            callback_log=callback_log
        )
        
        if exito:
            resultado['exitosos'] += 1
        else:
            resultado['fallidos'] += 1
            log(f"    {mensaje}")
        
        resultado['detalles'].append({
            'cliente': cliente,
            'nis': nis,
            'email': email_cliente,
            'exito': exito,
            'mensaje': mensaje
        })
    
    return resultado


# Función de prueba
def test_enviar_email():
    """Función para probar el envío de un email de prueba."""
    
    print("🧪 Probando envío de email...")
    
    exito, mensaje = enviar_email(
        destinatario="tu_email@ejemplo.com",  # CAMBIAR
        nombre_cliente="Cliente de Prueba",
        link_informe="https://ejemplo.com/informe.html",
        periodo="Febrero 2026",
        metricas={
            'consumo_total': 1234,
            'generacion': 567,
            'ahorro_estimado': 45000
        },
        callback_log=print
    )
    
    if exito:
        print("✅ Prueba exitosa!")
    else:
        print(f"❌ Prueba fallida: {mensaje}")


if __name__ == "__main__":
    test_enviar_email()
