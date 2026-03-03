#!/usr/bin/env python3
"""
Integraciones adicionales para Notion ERP
Slack, Gmail, Google Sheets, WhatsApp Business API
"""

import json
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import pandas as pd

from .logger import get_logger, get_error_handler
from .api_client import APIClient

class SlackIntegration:
    """Integración con Slack para notificaciones"""
    
    def __init__(self, webhook_url: str = None, bot_token: str = None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.logger = get_logger("SLACK")
        self.error_handler = get_error_handler()
        
        if webhook_url:
            self.client = APIClient(webhook_url, max_retries=3)
    
    def send_message(self, channel: str, message: str, 
                    blocks: List[Dict] = None, thread_ts: str = None) -> Dict:
        """Envía mensaje a Slack"""
        try:
            payload = {
                "channel": channel,
                "text": message
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            if thread_ts:
                payload["thread_ts"] = thread_ts
            
            if self.webhook_url:
                response = requests.post(self.webhook_url, json=payload)
                return {"success": response.status_code == 200, "response": response.json()}
            
            elif self.bot_token:
                headers = {"Authorization": f"Bearer {self.bot_token}"}
                response = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=headers,
                    json=payload
                )
                return response.json()
            
        except Exception as e:
            return self.error_handler.handle_exception(e, "enviar mensaje Slack")
    
    def send_alert(self, level: str, title: str, message: str, channel: str = "#alerts"):
        """Envía alerta formateada a Slack"""
        colors = {
            "critical": "#ff0000",
            "warning": "#ffaa00", 
            "info": "#0066cc"
        }
        
        color = colors.get(level, "#666666")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {title.upper()}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        return self.send_message(channel, f"🚨 {title}", blocks=blocks)
    
    def send_report(self, report_data: Dict, channel: str = "#reports"):
        """Envía reporte a Slack con formato"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 {report_data.get('title', 'Reporte ERP')}"
                }
            },
            {
                "type": "section",
                "fields": []
            }
        ]
        
        # Agregar métricas como campos
        for key, value in report_data.get("metrics", {}).items():
            blocks[1]["fields"].extend([
                {
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                }
            ])
        
        return self.send_message(channel, "📊 Reporte ERP", blocks=blocks)

class GmailIntegration:
    """Integración con Gmail para enviar emails"""
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.logger = get_logger("GMAIL")
        self.error_handler = get_error_handler()
    
    def send_email(self, to_emails: List[str], subject: str, body: str,
                   from_email: str = None, from_password: str = None,
                   is_html: bool = False, attachments: List[str] = None) -> Dict:
        """Envía email usando SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            
            # Agregar cuerpo
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Agregar attachments
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(attachment)
                    except Exception as e:
                        self.logger.warning(f"No se pudo adjuntar {file_path}: {e}")
            
            # Enviar email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(from_email, from_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            
            self.logger.success(f"Email enviado a {len(to_emails)} destinatarios")
            return {"success": True, "message": "Email enviado exitosamente"}
            
        except Exception as e:
            return self.error_handler.handle_exception(e, "enviar email Gmail")
    
    def send_report_email(self, report_data: Dict, to_emails: List[str],
                         from_email: str, from_password: str) -> Dict:
        """Envía reporte por email con formato HTML"""
        html_body = f"""
        <html>
        <body>
            <h2>📊 {report_data.get('title', 'Reporte ERP')}</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>📈 Métricas Principales</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                {"".join([f"<tr><td>{k}</td><td>{v}</td></tr>" 
                          for k, v in report_data.get('metrics', {}).items()])}
            </table>
            
            <h3>📝 Detalles</h3>
            <p>{report_data.get('details', 'Sin detalles adicionales')}</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to_emails=to_emails,
            subject=f"📊 {report_data.get('title', 'Reporte ERP')}",
            body=html_body,
            from_email=from_email,
            from_password=from_password,
            is_html=True
        )

class GoogleSheetsIntegration:
    """Integración con Google Sheets"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path
        self.logger = get_logger("GOOGLE_SHEETS")
        self.error_handler = get_error_handler()
        
        # Intentar importar gspread
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            self.gspread = gspread
            self.Credentials = Credentials
            self.available = True
        except ImportError:
            self.available = False
            self.logger.warning("gspread no instalado. Usa: pip install gspread google-auth-oauthlib")
    
    def export_to_sheet(self, data: List[Dict], sheet_name: str, 
                       worksheet_name: str = None) -> Dict:
        """Exporta datos a Google Sheet"""
        if not self.available:
            return {"success": False, "error": "google_sheets_not_available"}
        
        try:
            # Autenticar
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = self.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes)
            client = self.gspread.authorize(creds)
            
            # Abrir o crear spreadsheet
            try:
                spreadsheet = client.open(sheet_name)
            except self.gspread.SpreadsheetNotFound:
                spreadsheet = client.create(sheet_name)
            
            # Crear o seleccionar worksheet
            if worksheet_name:
                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                except self.gspread.WorksheetNotFound:
                    worksheet = spreadsheet.add_worksheet(
                        title=worksheet_name, 
                        rows=100, 
                        cols=20
                    )
            else:
                worksheet = spreadsheet.sheet1
            
            # Convertir datos a DataFrame y exportar
            df = pd.DataFrame(data)
            
            # Limpiar worksheet
            worksheet.clear()
            
            # Escribir headers
            headers = list(df.columns)
            worksheet.append_row(headers)
            
            # Escribir datos
            for _, row in df.iterrows():
                worksheet.append_row(list(row))
            
            # Compartir spreadsheet (opcional)
            # spreadsheet.share('user@example.com', perm_type='user', role='reader')
            
            self.logger.success(f"Datos exportados a {sheet_name}")
            return {
                "success": True,
                "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}",
                "rows_exported": len(data)
            }
            
        except Exception as e:
            return self.error_handler.handle_exception(e, "exportar a Google Sheets")
    
    def create_financial_dashboard(self, financial_data: Dict, 
                                  sheet_name: str = "ERP Dashboard") -> Dict:
        """Crea dashboard financiero en Google Sheets"""
        if not self.available:
            return {"success": False, "error": "google_sheets_not_available"}
        
        try:
            # Preparar datos para dashboard
            dashboard_data = []
            
            # Resumen de CxC
            for item in financial_data.get("cxc_summary", []):
                dashboard_data.append({
                    "Tipo": "Cuenta por Cobrar",
                    "Concepto": item.get("concepto"),
                    "Cliente": item.get("cliente"),
                    "Monto Total": item.get("monto_total"),
                    "Monto Cobrado": item.get("monto_cobrado"),
                    "Pendiente": item.get("pendiente"),
                    "Estado": item.get("estado"),
                    "Vencimiento": item.get("vencimiento")
                })
            
            # Resumen de CxP
            for item in financial_data.get("cxp_summary", []):
                dashboard_data.append({
                    "Tipo": "Cuenta por Pagar",
                    "Proveedor": item.get("proveedor"),
                    "Categoría": item.get("categoria"),
                    "Monto": item.get("monto"),
                    "Estado": item.get("estado"),
                    "Vencimiento": item.get("vencimiento")
                })
            
            return self.export_to_sheet(dashboard_data, sheet_name, "Dashboard")
            
        except Exception as e:
            return self.error_handler.handle_exception(e, "crear dashboard Google Sheets")

class WhatsAppBusinessIntegration:
    """Integración con WhatsApp Business API"""
    
    def __init__(self, access_token: str, phone_number_id: str, api_version: str = "v18.0"):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.logger = get_logger("WHATSAPP")
        self.error_handler = get_error_handler()
    
    def send_message(self, to: str, message: str, message_type: str = "text") -> Dict:
        """Envía mensaje por WhatsApp"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": message_type,
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                self.logger.success(f"WhatsApp enviado a {to}")
                return {"success": True, "data": response.json()}
            else:
                return self.error_handler.handle_api_error(
                    type('Response', (), {'status_code': response.status_code, 'text': response.text})(),
                    "enviar WhatsApp"
                )
                
        except Exception as e:
            return self.error_handler.handle_exception(e, "enviar WhatsApp")
    
    def send_payment_reminder(self, to: str, client_name: str, 
                            amount: float, due_date: str) -> Dict:
        """Envía recordatorio de pago por WhatsApp"""
        message = f"""💰 Recordatorio de Pago
        
Estimado/a {client_name},

Le recordamos que tiene un pago pendiente:
• Monto: ${amount:,.2f}
• Vencimiento: {due_date}

Para realizar el pago, puede contactarnos por este medio o transferir a nuestra cuenta bancaria.

¡Gracias por su preferencia! 🙏"""
        
        return self.send_message(to, message)
    
    def send_project_update(self, to: str, project_name: str, 
                          status: str, details: str = "") -> Dict:
        """Envía actualización de proyecto por WhatsApp"""
        message = f"""🏗️ Actualización de Proyecto

Proyecto: {project_name}
Estado: {status}

{details}

Para más detalles, no dude en contactarnos."""
        
        return self.send_message(to, message)

# Integraciones manager
class IntegrationsManager:
    """Gestor central de todas las integraciones"""
    
    def __init__(self):
        self.logger = get_logger("INTEGRATIONS")
        self.slack = None
        self.gmail = None
        self.google_sheets = None
        self.whatsapp = None
        
        # Cargar configuración desde settings
        self._load_integrations()
    
    def _load_integrations(self):
        """Carga integraciones basadas en configuración"""
        try:
            from config.settings import config
            
            # Inicializar solo si hay configuración
            if hasattr(config, 'SLACK_WEBHOOK_URL') and config.SLACK_WEBHOOK_URL:
                self.slack = SlackIntegration(webhook_url=config.SLACK_WEBHOOK_URL)
                self.logger.info("✅ Slack integración inicializada")
            
            if hasattr(config, 'GMAIL_CREDENTIALS') and config.GMAIL_CREDENTIALS:
                self.gmail = GmailIntegration()
                self.logger.info("✅ Gmail integración inicializada")
            
            if hasattr(config, 'GOOGLE_SHEETS_CREDENTIALS') and config.GOOGLE_SHEETS_CREDENTIALS:
                self.google_sheets = GoogleSheetsIntegration(config.GOOGLE_SHEETS_CREDENTIALS)
                self.logger.info("✅ Google Sheets integración inicializada")
            
            if (hasattr(config, 'WHATSAPP_ACCESS_TOKEN') and 
                hasattr(config, 'WHATSAPP_PHONE_NUMBER_ID')):
                self.whatsapp = WhatsAppBusinessIntegration(
                    config.WHATSAPP_ACCESS_TOKEN,
                    config.WHATSAPP_PHONE_NUMBER_ID
                )
                self.logger.info("✅ WhatsApp integración inicializada")
                
        except Exception as e:
            self.logger.error("Error cargando integraciones", e)
    
    def send_notification(self, message: str, channels: List[str] = None, **kwargs):
        """Envía notificación a múltiples canales"""
        results = {}
        
        if not channels:
            channels = []
        
        # Slack
        if "slack" in channels and self.slack:
            results["slack"] = self.slack.send_message("#general", message, **kwargs)
        
        # Email
        if "email" in channels and self.gmail:
            to_emails = kwargs.get("to_emails", [])
            if to_emails:
                results["email"] = self.gmail.send_email(
                    to_emails=to_emails,
                    subject="📢 Notificación ERP",
                    body=message,
                    **kwargs
                )
        
        # WhatsApp
        if "whatsapp" in channels and self.whatsapp:
            to_phone = kwargs.get("to_phone")
            if to_phone:
                results["whatsapp"] = self.whatsapp.send_message(to_phone, message)
        
        return results

# Instancia global
integrations_manager = IntegrationsManager()

def get_integrations_manager() -> IntegrationsManager:
    """Obtiene instancia del gestor de integraciones"""
    return integrations_manager

if __name__ == "__main__":
    """Prueba de integraciones"""
    print("🧪 Probando sistema de integraciones...")
    
    manager = get_integrations_manager()
    print("✅ Gestor de integraciones inicializado")
    
    # Probar envío de notificación
    # manager.send_notification("🧪 Mensaje de prueba", channels=["slack"])
    
    print("📝 Configura tus credenciales en config/settings.py para activar integraciones")