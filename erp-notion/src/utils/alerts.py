#!/usr/bin/env python3
"""
Sistema avanzado de alertas y notificaciones para Notion ERP
Integración con múltiples canales y reglas personalizadas
"""

import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import time
import requests

from .logger import get_logger, get_error_handler
from .monitoring import get_monitoring_system
from .integrations import get_integrations_manager

class AlertLevel(Enum):
    """Niveles de alerta"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Canales de notificación"""
    EMAIL = "email"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    WEBHOOK = "webhook"
    LOG = "log"
    DASHBOARD = "dashboard"

@dataclass
class Alert:
    """Estructura de una alerta"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    data: Dict[str, Any] = None
    acknowledged: bool = False
    resolved: bool = False
    channels: List[AlertChannel] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.channels is None:
            self.channels = [AlertChannel.LOG]

@dataclass
class AlertRule:
    """Regla para generar alertas automáticas"""
    id: str
    name: str
    description: str
    condition: Callable[[Dict], bool]
    level: AlertLevel
    message_template: str
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None

class AlertManager:
    """Gestor central de alertas"""
    
    def __init__(self):
        self.logger = get_logger("ALERTS")
        self.error_handler = get_error_handler()
        self.monitoring = get_monitoring_system()
        self.integrations = get_integrations_manager()
        
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self.alert_history: List[Alert] = []
        
        # Configuración
        self.max_alerts = 1000
        self.max_history = 5000
        self.cooldown_tracker = {}
        
        # Directorios
        Path("data/alerts").mkdir(parents=True, exist_ok=True)
        
        # Inicializar reglas por defecto
        self._initialize_default_rules()
        
        # Thread para procesamiento asíncrono
        self.processing_thread = None
        self.stop_processing = False
        
    def _initialize_default_rules(self):
        """Inicializa reglas de alerta por defecto"""
        
        # Regla: Alta tasa de errores
        self.add_rule(AlertRule(
            id="high_error_rate",
            name="Alta Tasa de Errores",
            description="Alerta cuando la tasa de errores supera el 10%",
            condition=lambda metrics: metrics.get("error_rate", 0) > 0.1,
            level=AlertLevel.WARNING,
            message_template="🚨 Tasa de errores elevada: {error_rate:.1%} ({failed_operations} operaciones fallidas)",
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.DASHBOARD],
            cooldown_minutes=30
        ))
        
        # Regla: Monto pendiente alto
        self.add_rule(AlertRule(
            id="high_pending_amount",
            name="Monto Pendiente Elevado",
            description="Alerta cuando el monto pendiente supera $1M",
            condition=lambda metrics: metrics.get("pending_amount", 0) > 1000000,
            level=AlertLevel.WARNING,
            message_template="💰 Monto pendiente elevado: ${pending_amount:,.2f}",
            channels=[AlertChannel.SLACK, AlertChannel.DASHBOARD],
            cooldown_minutes=60
        ))
        
        # Regla: Múltiples operaciones fallidas
        self.add_rule(AlertRule(
            id="multiple_failures",
            name="Múltiples Fallos",
            description="Alerta cuando hay múltiples operaciones fallidas consecutivas",
            condition=lambda metrics: metrics.get("failed_operations", 0) > 5,
            level=AlertLevel.ERROR,
            message_template="❌ Múltiples operaciones fallidas: {failed_operations} falllos en el último período",
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.WHATSAPP],
            cooldown_minutes=15
        ))
        
        # Regla: API lenta
        self.add_rule(AlertRule(
            id="slow_api_response",
            name="API Lenta",
            description="Alerta cuando el tiempo de respuesta de API es alto",
            condition=lambda metrics: metrics.get("api_response_time_avg", 0) > 5.0,
            level=AlertLevel.WARNING,
            message_template="⏱️ Tiempo de respuesta API elevado: {api_response_time_avg:.2f}s",
            channels=[AlertChannel.SLACK, AlertChannel.DASHBOARD],
            cooldown_minutes=20
        ))
    
    def create_alert(self, level: AlertLevel, title: str, message: str, 
                    source: str = "manual", data: Dict = None, 
                    channels: List[AlertChannel] = None) -> str:
        """Crea una nueva alerta"""
        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            data=data or {},
            channels=channels or [AlertChannel.LOG]
        )
        
        self.alerts.append(alert)
        self.alert_history.append(alert)
        
        # Limitar tamaño de listas
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Procesar alerta
        self._process_alert(alert)
        
        self.logger.info(f"🚨 Alerta creada: {level.value.upper()} - {title}")
        
        return alert_id
    
    def add_rule(self, rule: AlertRule):
        """Agrega una regla de alerta"""
        # Verificar si ya existe
        existing_rule = next((r for r in self.rules if r.id == rule.id), None)
        if existing_rule:
            self.rules = [r for r in self.rules if r.id != rule.id]
        
        self.rules.append(rule)
        self.logger.info(f"✅ Regla de alerta agregada: {rule.name}")
    
    def evaluate_rules(self, metrics_data: Dict = None):
        """Evalúa todas las reglas activas"""
        if metrics_data is None:
            metrics_data = self.monitoring.get_dashboard_data().get("current_metrics", {})
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                # Verificar cooldown
                if self._is_rule_in_cooldown(rule):
                    continue
                
                # Evaluar condición
                if rule.condition(metrics_data):
                    # Formatear mensaje
                    message = rule.message_template.format(**metrics_data)
                    
                    # Crear alerta
                    self.create_alert(
                        level=rule.level,
                        title=f"🤖 {rule.name}",
                        message=message,
                        source=f"rule:{rule.id}",
                        data={"rule_id": rule.id, "metrics": metrics_data},
                        channels=rule.channels
                    )
                    
                    # Actualizar cooldown
                    rule.last_triggered = datetime.now()
                    self.cooldown_tracker[rule.id] = datetime.now()
                    
            except Exception as e:
                self.logger.error(f"Error evaluando regla {rule.id}", e)
    
    def _is_rule_in_cooldown(self, rule: AlertRule) -> bool:
        """Verifica si una regla está en cooldown"""
        if rule.cooldown_minutes <= 0:
            return False
        
        last_trigger = rule.last_triggered or self.cooldown_tracker.get(rule.id)
        if not last_trigger:
            return False
        
        cooldown_end = last_trigger + timedelta(minutes=rule.cooldown_minutes)
        return datetime.now() < cooldown_end
    
    def _process_alert(self, alert: Alert):
        """Procesa una alerta y envía notificaciones"""
        try:
            for channel in alert.channels:
                self._send_notification(alert, channel)
                
        except Exception as e:
            self.logger.error(f"Error procesando alerta {alert.id}", e)
    
    def _send_notification(self, alert: Alert, channel: AlertChannel):
        """Envía notificación por canal específico"""
        try:
            if channel == AlertChannel.LOG:
                self._log_alert(alert)
                
            elif channel == AlertChannel.SLACK:
                self._send_slack_notification(alert)
                
            elif channel == AlertChannel.EMAIL:
                self._send_email_notification(alert)
                
            elif channel == AlertChannel.WHATSAPP:
                self._send_whatsapp_notification(alert)
                
            elif channel == AlertChannel.WEBHOOK:
                self._send_webhook_notification(alert)
                
            elif channel == AlertChannel.DASHBOARD:
                # Las alertas de dashboard se guardan automáticamente
                pass
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación por {channel.value}", e)
    
    def _log_alert(self, alert: Alert):
        """Registra alerta en logs"""
        level_map = {
            AlertLevel.DEBUG: "DEBUG",
            AlertLevel.INFO: "INFO", 
            AlertLevel.WARNING: "WARNING",
            AlertLevel.ERROR: "ERROR",
            AlertLevel.CRITICAL: "CRITICAL"
        }
        
        log_message = f"[ALERT] {alert.title}: {alert.message}"
        getattr(self.logger, level_map[alert.level].lower())(log_message, alert.data)
    
    def _send_slack_notification(self, alert: Alert):
        """Envía notificación a Slack"""
        if not self.integrations.slack:
            return
        
        level_emojis = {
            AlertLevel.DEBUG: "🐛",
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌", 
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emojis.get(alert.level, "📢")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            }
        ]
        
        if alert.data:
            data_fields = []
            for key, value in alert.data.items():
                data_fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:* {value}"
                })
            
            blocks.append({
                "type": "section",
                "fields": data_fields
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | 🏷️ {alert.source}"
                }
            ]
        })
        
        self.integrations.slack.send_message("#alerts", f"{emoji} {alert.title}", blocks=blocks)
    
    def _send_email_notification(self, alert: Alert):
        """Envía notificación por email"""
        if not self.integrations.gmail:
            return
        
        # Enviar solo para alertas de alto nivel
        if alert.level in [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]:
            subject = f"🚨 Alerta ERP: {alert.title}"
            
            html_body = f"""
            <h2>{alert.title}</h2>
            <p><strong>Nivel:</strong> {alert.level.value.upper()}</p>
            <p><strong>Mensaje:</strong> {alert.message}</p>
            <p><strong>Origen:</strong> {alert.source}</p>
            <p><strong>Fecha:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            {f'<h3>Datos Adicionales:</h3><pre>{json.dumps(alert.data, indent=2)}</pre>' if alert.data else ''}
            """
            
            # Configurar destinatarios desde settings
            from config.settings import config
            recipients = getattr(config, 'ALERT_EMAIL_RECIPIENTS', [])
            
            if recipients:
                self.integrations.gmail.send_email(
                    to_emails=recipients,
                    subject=subject,
                    body=html_body,
                    is_html=True
                )
    
    def _send_whatsapp_notification(self, alert: Alert):
        """Envía notificación por WhatsApp"""
        if not self.integrations.whatsapp:
            return
        
        # Solo para alertas críticas
        if alert.level == AlertLevel.CRITICAL:
            message = f"🚨 {alert.title}\n\n{alert.message}\n\n📅 {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Configurar números desde settings
            from config.settings import config
            phone_numbers = getattr(config, 'ALERT_WHATSAPP_NUMBERS', [])
            
            for phone in phone_numbers:
                self.integrations.whatsapp.send_message(phone, message)
    
    def _send_webhook_notification(self, alert: Alert):
        """Envía notificación via webhook"""
        from config.settings import config
        webhook_url = getattr(config, 'ALERT_WEBHOOK_URL', None)
        
        if not webhook_url:
            return
        
        payload = {
            "alert_id": alert.id,
            "level": alert.level.value,
            "title": alert.title,
            "message": alert.message,
            "source": alert.source,
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.data
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.debug(f"Webhook notification sent for alert {alert.id}")
            else:
                self.logger.warning(f"Webhook notification failed: {response.status_code}")
        except Exception as e:
            self.logger.error("Error sending webhook notification", e)
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Reconoce una alerta"""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert:
            alert.acknowledged = True
            alert.data["acknowledged_by"] = user
            alert.data["acknowledged_at"] = datetime.now().isoformat()
            self.logger.info(f"✅ Alerta {alert_id} reconocida por {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution: str = "resolved", 
                     user: str = "system") -> bool:
        """Resuelve una alerta"""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert:
            alert.resolved = True
            alert.data["resolved_by"] = user
            alert.data["resolved_at"] = datetime.now().isoformat()
            alert.data["resolution"] = resolution
            self.logger.info(f"✅ Alerta {alert_id} resuelta por {user}: {resolution}")
            return True
        return False
    
    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Obtiene alertas activas"""
        active_alerts = [a for a in self.alerts if not a.resolved]
        
        if level:
            active_alerts = [a for a in active_alerts if a.level == level]
        
        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de alertas"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]
        week_alerts = [a for a in self.alert_history if a.timestamp > last_7d]
        
        stats = {
            "total_alerts": len(self.alert_history),
            "active_alerts": len(self.get_active_alerts()),
            "acknowledged_alerts": len([a for a in self.alerts if a.acknowledged and not a.resolved]),
            "resolved_alerts": len([a for a in self.alerts if a.resolved]),
            "last_24h": {
                "total": len(recent_alerts),
                "by_level": {
                    level.value: len([a for a in recent_alerts if a.level == level])
                    for level in AlertLevel
                }
            },
            "last_7d": {
                "total": len(week_alerts),
                "by_level": {
                    level.value: len([a for a in week_alerts if a.level == level])
                    for level in AlertLevel
                }
            },
            "rules_active": len([r for r in self.rules if r.enabled]),
            "rules_total": len(self.rules)
        }
        
        return stats
    
    def start_automated_monitoring(self, interval_seconds: int = 60):
        """Inicia monitoreo automatizado con evaluación de reglas"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("⚠️ Monitoreo automatizado ya está activo")
            return
        
        self.stop_processing = False
        self.processing_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.processing_thread.start()
        self.logger.info(f"🚀 Monitoreo automatizado iniciado (intervalo: {interval_seconds}s)")
    
    def stop_automated_monitoring(self):
        """Detiene monitoreo automatizado"""
        self.stop_processing = True
        if self.processing_thread:
            self.processing_thread.join()
        self.logger.info("🛑 Monitoreo automatizado detenido")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Bucle principal de monitoreo"""
        while not self.stop_processing:
            try:
                # Evaluar reglas con métricas actuales
                self.evaluate_rules()
                
                # Esperar siguiente intervalo
                time.sleep(interval_seconds)
                
            except Exception as e:
                self.logger.error("Error en bucle de monitoreo", e)
                time.sleep(interval_seconds)
    
    def save_alerts(self):
        """Guarda alertas en archivo"""
        try:
            alerts_data = []
            for alert in self.alerts:
                alert_dict = asdict(alert)
                alert_dict["timestamp"] = alert.timestamp.isoformat()
                alert_dict["level"] = alert.level.value
                alert_dict["channels"] = [c.value for c in alert.channels]
                alerts_data.append(alert_dict)
            
            with open("data/alerts/current_alerts.json", "w", encoding="utf-8") as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)
            
            # Guardar estadísticas
            stats = self.get_alert_stats()
            with open("data/alerts/alert_stats.json", "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("✅ Alertas guardadas en archivo")
            
        except Exception as e:
            self.logger.error("Error guardando alertas", e)

# Instancia global
alert_manager = AlertManager()

def get_alert_manager() -> AlertManager:
    """Obtiene instancia del gestor de alertas"""
    return alert_manager

# Funciones de conveniencia
def create_alert(level: AlertLevel, title: str, message: str, **kwargs) -> str:
    """Función de conveniencia para crear alertas"""
    return get_alert_manager().create_alert(level, title, message, **kwargs)

def create_info_alert(title: str, message: str, **kwargs) -> str:
    """Crea alerta de información"""
    return create_alert(AlertLevel.INFO, title, message, **kwargs)

def create_warning_alert(title: str, message: str, **kwargs) -> str:
    """Crea alerta de advertencia"""
    return create_alert(AlertLevel.WARNING, title, message, **kwargs)

def create_error_alert(title: str, message: str, **kwargs) -> str:
    """Crea alerta de error"""
    return create_alert(AlertLevel.ERROR, title, message, **kwargs)

def create_critical_alert(title: str, message: str, **kwargs) -> str:
    """Crea alerta crítica"""
    return create_alert(AlertLevel.CRITICAL, title, message, **kwargs)

if __name__ == "__main__":
    """Prueba del sistema de alertas"""
    print("🚀 Probando sistema de alertas...")
    
    alert_manager = get_alert_manager()
    
    # Probar creación de alertas
    alert_id = create_info_alert(
        "Prueba de Sistema", 
        "Este es un mensaje de prueba del sistema de alertas",
        data={"test": True, "timestamp": datetime.now().isoformat()}
    )
    
    print(f"✅ Alerta creada: {alert_id}")
    
    # Probar evaluación de reglas
    alert_manager.evaluate_rules({
        "error_rate": 0.15,
        "failed_operations": 7,
        "pending_amount": 1500000
    })
    
    print("✅ Reglas evaluadas")
    
    # Mostrar estadísticas
    stats = alert_manager.get_alert_stats()
    print(f"📊 Estadísticas: {stats['active_alerts']} alertas activas")
    
    print("🔔 Configura tus canales de notificación para recibir alertas")