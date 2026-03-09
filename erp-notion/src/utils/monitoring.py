#!/usr/bin/env python3
"""
Sistema de monitoreo y métricas para Notion ERP
Proporciona dashboards y alertas en tiempo real
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

from .logger import get_logger
from .api_client import NotionAPIClient, TrelloAPIClient

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    timestamp: datetime
    notion_api_calls: int = 0
    trello_api_calls: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_projects: int = 0
    total_cxc: int = 0
    total_cxp: int = 0
    pending_amount: float = 0.0
    processed_amount: float = 0.0
    api_response_time_avg: float = 0.0
    error_rate: float = 0.0

@dataclass 
class AlertLevel:
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class MonitoringSystem:
    """Sistema centralizado de monitoreo"""
    
    def __init__(self):
        self.logger = get_logger("MONITORING")
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Dict] = []
        self.active = False
        self.monitoring_thread = None
        
        # Umbrales para alertas
        self.thresholds = {
            "error_rate": 0.1,  # 10%
            "api_response_time": 5.0,  # 5 segundos
            "pending_amount_threshold": 1000000,  # $1M
            "max_failed_operations": 5
        }
        
        # Crear directorios
        Path("data/metrics").mkdir(parents=True, exist_ok=True)
        Path("data/dashboards").mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Inicia monitoreo continuo"""
        if self.active:
            self.logger.warning("⚠️ Monitoreo ya está activo")
            return
            
        self.active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("🚀 Sistema de monitoreo iniciado", {"interval": interval_seconds})
    
    def stop_monitoring(self):
        """Detiene monitoreo"""
        self.active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.logger.info("🛑 Sistema de monitoreo detenido")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Bucle principal de monitoreo"""
        while self.active:
            try:
                metrics = self.collect_metrics()
                self.analyze_metrics(metrics)
                self.save_metrics(metrics)
                time.sleep(interval_seconds)
            except Exception as e:
                self.logger.error("❌ Error en bucle de monitoreo", e)
                time.sleep(interval_seconds)
    
    def collect_metrics(self) -> SystemMetrics:
        """Colecciona métricas actuales del sistema"""
        timestamp = datetime.now()
        
        # Leer métricas de logs y APIs
        metrics = SystemMetrics(timestamp=timestamp)
        
        # Contar llamadas API de logs
        try:
            log_files = list(Path("logs").glob("erp_*.log"))
            for log_file in log_files:
                if log_file.stat().st_mtime > (timestamp - timedelta(minutes=5)).timestamp():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        metrics.notion_api_calls += content.count("api.notion.com")
                        metrics.trello_api_calls += content.count("api.trello.com")
                        
                        # Contar operaciones exitosas/fallidas
                        metrics.successful_operations += content.count("✅")
                        metrics.failed_operations += content.count("❌")
        except Exception as e:
            self.logger.error("Error leyendo logs para métricas", e)
        
        # Obtener métricas de Notion
        try:
            from config.settings import config
            notion_client = NotionAPIClient(config.NOTION_TOKEN)
            
            # Contar proyectos
            projects_response = notion_client.query_database(config.CENTROS_DB_ID)
            if projects_response["success"]:
                metrics.total_projects = len(projects_response["data"].get("results", []))
            
            # Contar CxC
            cxc_response = notion_client.query_database("2e0c81c3-5804-815a-8755-f4f254257f6a")
            if cxc_response["success"]:
                cxc_data = cxc_response["data"].get("results", [])
                metrics.total_cxc = len(cxc_data)
                
                # Calcular montos pendientes/procesados
                for item in cxc_data:
                    properties = item.get("properties", {})
                    monto_total = properties.get("Monto Total", {}).get("number", 0)
                    monto_cobrado = properties.get("Monto Cobrado", {}).get("number", 0)
                    
                    metrics.processed_amount += monto_cobrado
                    metrics.pending_amount += (monto_total - monto_cobrado)
            
        except Exception as e:
            self.logger.error("Error obteniendo métricas de Notion", e)
        
        # Calcular métricas derivadas
        total_operations = metrics.successful_operations + metrics.failed_operations
        if total_operations > 0:
            metrics.error_rate = metrics.failed_operations / total_operations
        
        self.metrics_history.append(metrics)
        return metrics
    
    def analyze_metrics(self, metrics: SystemMetrics):
        """Analiza métricas y genera alertas"""
        # Verificar tasa de error
        if metrics.error_rate > self.thresholds["error_rate"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Alta tasa de errores",
                f"Tasa de error: {metrics.error_rate:.1%}",
                {"error_rate": metrics.error_rate}
            )
        
        # Verificar monto pendiente alto
        if metrics.pending_amount > self.thresholds["pending_amount_threshold"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Monto pendiente elevado",
                f"${metrics.pending_amount:,.2f} pendientes de cobro",
                {"pending_amount": metrics.pending_amount}
            )
        
        # Verificar operaciones fallidas
        if metrics.failed_operations > self.thresholds["max_failed_operations"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "Múltiples operaciones fallidas",
                f"{metrics.failed_operations} operaciones fallaron",
                {"failed_operations": metrics.failed_operations}
            )
    
    def create_alert(self, level: str, title: str, message: str, data: Dict = None):
        """Crea una nueva alerta"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "message": message,
            "data": data or {}
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"🚨 ALERTA [{level.upper()}] {title}: {message}", data)
        
        # Mantener solo últimas 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def save_metrics(self, metrics: SystemMetrics):
        """Guarda métricas en archivo JSON"""
        try:
            # Convertir datetime a string para JSON
            metrics_dict = asdict(metrics)
            metrics_dict["timestamp"] = metrics.timestamp.isoformat()
            
            # Guardar métricas actuales
            with open("data/metrics/current_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics_dict, f, indent=2, ensure_ascii=False)
            
            # Guardar histórico (últimas 24 horas)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
            history_data = []
            for m in recent_metrics:
                m_dict = asdict(m)
                m_dict["timestamp"] = m.timestamp.isoformat()
                history_data.append(m_dict)
            
            with open("data/metrics/metrics_history.json", "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error("Error guardando métricas", e)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos para dashboard"""
        if not self.metrics_history:
            return {}
        
        latest_metrics = self.metrics_history[-1]
        
        dashboard_data = {
            "last_updated": latest_metrics.timestamp.isoformat(),
            "current_metrics": asdict(latest_metrics),
            "recent_alerts": self.alerts[-10:],  # Últimas 10 alertas
            "trends": self._calculate_trends(),
            "summary": {
                "total_projects": latest_metrics.total_projects,
                "total_cxc": latest_metrics.total_cxc,
                "pending_amount": latest_metrics.pending_amount,
                "success_rate": 1 - latest_metrics.error_rate if latest_metrics.error_rate < 1 else 0
            }
        }
        
        # Reemplazar datetime con string en current_metrics
        dashboard_data["current_metrics"]["timestamp"] = latest_metrics.timestamp.isoformat()
        
        return dashboard_data
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calcula tendencias basadas en métricas históricas"""
        if len(self.metrics_history) < 2:
            return {}
        
        current = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        trends = {}
        
        # Calcular cambios porcentuales
        if previous.total_projects > 0:
            trends["projects_change"] = (current.total_projects - previous.total_projects) / previous.total_projects
        
        if previous.total_cxc > 0:
            trends["cxc_change"] = (current.total_cxc - previous.total_cxc) / previous.total_cxc
        
        if previous.pending_amount > 0:
            trends["pending_change"] = (current.pending_amount - previous.pending_amount) / previous.pending_amount
        
        return trends
    
    def generate_dashboard_html(self) -> str:
        """Genera dashboard HTML"""
        data = self.get_dashboard_data()
        
        html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notion ERP Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px 20px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2196F3; }
        .metric-label { color: #666; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert.critical { background: #ffebee; border-left: 4px solid #f44336; }
        .alert.warning { background: #fff3e0; border-left: 4px solid #ff9800; }
        .alert.info { background: #e3f2fd; border-left: 4px solid #2196F3; }
        .status { color: #4CAF50; }
        .status.warning { color: #ff9800; }
        .status.error { color: #f44336; }
        .header { text-align: center; margin-bottom: 30px; }
        .refresh-btn { background: #2196F3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #1976D2; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🚀 Notion ERP Dashboard</h1>
            <p>Última actualización: {last_updated}</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Actualizar</button>
        </div>
        
        <div class="card">
            <h2>📊 Métricas Principales</h2>
            <div class="metric">
                <div class="metric-value">{total_projects}</div>
                <div class="metric-label">Proyectos Totales</div>
            </div>
            <div class="metric">
                <div class="metric-value">{total_cxc}</div>
                <div class="metric-label">Cuentas por Cobrar</div>
            </div>
            <div class="metric">
                <div class="metric-value">${pending_amount:,.0f}</div>
                <div class="metric-label">Monto Pendiente</div>
            </div>
            <div class="metric">
                <div class="metric-value success-rate">{success_rate:.1%}</div>
                <div class="metric-label">Tasa de Éxito</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🚨 Alertas Recientes</h2>
            {alerts_html}
        </div>
        
        <div class="card">
            <h2>⚡ Estado del Sistema</h2>
            <div class="metric">
                <div class="metric-value {success_rate_class}">{success_rate:.1%}</div>
                <div class="metric-label">Tasa de Éxito</div>
            </div>
            <div class="metric">
                <div class="metric-value">{api_calls}</div>
                <div class="metric-label">Llamadas API</div>
            </div>
            <div class="metric">
                <div class="metric-value">{response_time:.1f}s</div>
                <div class="metric-label">Tiempo Resp. API</div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh cada 30 segundos
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
        """.format(
            last_updated=data.get("last_updated", "N/A"),
            total_projects=data.get("current_metrics", {}).get("total_projects", 0),
            total_cxc=data.get("current_metrics", {}).get("total_cxc", 0),
            pending_amount=data.get("current_metrics", {}).get("pending_amount", 0),
            success_rate=data.get("summary", {}).get("success_rate", 0),
            alerts_html=self._generate_alerts_html(data.get("recent_alerts", [])),
            api_calls=data.get("current_metrics", {}).get("notion_api_calls", 0) + data.get("current_metrics", {}).get("trello_api_calls", 0),
            response_time=data.get("current_metrics", {}).get("api_response_time_avg", 0),
            success_rate_class="status" if data.get("summary", {}).get("success_rate", 0) > 0.9 else "status warning" if data.get("summary", {}).get("success_rate", 0) > 0.7 else "status error"
        )
        
        return html_template
    
    def _generate_alerts_html(self, alerts: List[Dict]) -> str:
        """Genera HTML para alertas"""
        if not alerts:
            return "<p>✅ No hay alertas recientes</p>"
        
        alerts_html = ""
        for alert in alerts:
            alerts_html += f'''
            <div class="alert {alert['level']}">
                <strong>{alert['title']}</strong><br>
                {alert['message']}<br>
                <small>{alert['timestamp']}</small>
            </div>
            '''
        
        return alerts_html
    
    def save_dashboard(self):
        """Guarda dashboard HTML"""
        try:
            html_content = self.generate_dashboard_html()
            with open("data/dashboards/dashboard.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info("✅ Dashboard guardado en data/dashboards/dashboard.html")
        except Exception as e:
            self.logger.error("Error guardando dashboard", e)

# Instancia global del sistema de monitoreo
monitoring_system = MonitoringSystem()

def get_monitoring_system() -> MonitoringSystem:
    """Obtiene instancia del sistema de monitoreo"""
    return monitoring_system

if __name__ == "__main__":
    """Prueba del sistema de monitoreo"""
    print("🚀 Iniciando prueba del sistema de monitoreo...")
    
    monitoring = get_monitoring_system()
    monitoring.collect_metrics()
    monitoring.save_dashboard()
    
    print("✅ Sistema de monitoreo probado")
    print("📊 Dashboard disponible en: data/dashboards/dashboard.html")