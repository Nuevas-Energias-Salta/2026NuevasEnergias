#!/usr/bin/env python3
"""
API endpoint para el dashboard del ERP
Proporciona datos en tiempo real para el dashboard HTML
"""

import json
import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.monitoring import get_monitoring_system
from src.utils.alerts import get_alert_manager
from src.utils.performance import get_performance_optimizer
from src.utils.api_client import NotionAPIClient
from config.settings import config

class DashboardAPI(BaseHTTPRequestHandler):
    """Handler para la API del dashboard"""
    
    # Cache para métricas (5 minutos)
    _metrics_cache = {}
    _cache_timestamp = None
    _cache_duration = 300  # 5 minutos
    
    def __init__(self, *args, **kwargs):
        self.monitoring = get_monitoring_system()
        self.alert_manager = get_alert_manager()
        self.optimizer = get_performance_optimizer()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Manejar peticiones GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/dashboard':
            self.handle_dashboard_request(parsed_path)
        elif parsed_path.path == '/api/metrics':
            self.handle_metrics_request()
        elif parsed_path.path == '/api/alerts':
            self.handle_alerts_request()
        elif parsed_path.path == '/api/health':
            self.handle_health_request()
        elif parsed_path.path == '/':
            self.serve_dashboard()
        else:
            self.send_error(404, "Not Found")
    
    def handle_dashboard_request(self, parsed_path):
        """Manejar petición principal del dashboard"""
        try:
            # Obtener datos del sistema
            dashboard_data = self.monitoring.get_dashboard_data()
            alerts = self.alert_manager.get_active_alerts()
            performance_data = self.optimizer.get_performance_report()
            
            # Obtener métricas de Notion
            notion_metrics = self.get_notion_metrics()
            
            # Obtener métricas de caché
            cache_stats = self.optimizer.cache_manager.get_stats()
            
            # Combinar datos
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "projects_total": notion_metrics.get("projects", 0),
                    "cxc_total": notion_metrics.get("cxc", 0),
                    "cxp_total": notion_metrics.get("cxp", 0),
                    "pending_amount": notion_metrics.get("pending_amount", 0),
                    "total_revenue": notion_metrics.get("total_revenue", 0),
                    "total_expenses": notion_metrics.get("total_expenses", 0),
                    "net_profit": notion_metrics.get("net_profit", 0),
                    "success_rate": dashboard_data.get("current_metrics", {}).get("success_rate", 100),
                    "system_health": 100,  # Podríamos calcular esto basado en componentes
                    "api_calls": dashboard_data.get("current_metrics", {}).get("api_calls", 0),
                    "api_response_time": dashboard_data.get("current_metrics", {}).get("avg_response_time", 0.0),
                    "cache_hit_rate": cache_stats.get("hit_rate", 0) * 100
                },
                "alerts": [
                    {
                        "level": alert.level.value,
                        "title": alert.title,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    } for alert in alerts[:10]
                ],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "Sistema de Logging", "status": "active"},
                        {"name": "Gestor de Caché", "status": "active"},
                        {"name": "Sistema de Monitoreo", "status": "active"},
                        {"name": "Gestor de Alertas", "status": "active"},
                        {"name": "Optimizador de Rendimiento", "status": "active"}
                    ],
                    "performance": performance_data.get("summary", {}),
                    "cache_stats": cache_stats
                },
                "recent_activity": self.get_recent_activity()
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            print(f"Error en dashboard request: {e}")
            self.send_error(500, f"Internal Server Error: {e}")
    
    def handle_metrics_request(self):
        """Manejar petición de métricas"""
        try:
            metrics = self.monitoring.get_dashboard_data()
            self.send_json_response(metrics)
        except Exception as e:
            self.send_error(500, f"Error getting metrics: {e}")
    
    def handle_alerts_request(self):
        """Manejar petición de alertas"""
        try:
            alerts = self.alert_manager.get_active_alerts()
            alerts_data = [
                {
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                } for alert in alerts
            ]
            self.send_json_response({"alerts": alerts_data})
        except Exception as e:
            self.send_error(500, f"Error getting alerts: {e}")
    
    def handle_health_request(self):
        """Manejar petición de health check"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "uptime": "operational",
                "cache_status": {
                    "cached": self._metrics_cache is not None,
                    "last_update": self._cache_timestamp
                },
                "services": {
                    "monitoring": "active",
                    "alerts": "active", 
                    "performance_optimizer": "active",
                    "notion_api": "connected"
                }
            }
            self.send_json_response(health_status)
        except Exception as e:
            self.send_error(500, f"Health check failed: {e}")
    
    def get_notion_metrics(self):
        """Obtener métricas de Notion con caché y optimización"""
        # Verificar caché
        current_time = time.time()
        if (self._metrics_cache and self._cache_timestamp and 
            current_time - self._cache_timestamp < self._cache_duration):
            self.monitoring.logger.info("Usando métricas en caché")
            return self._metrics_cache
        
        try:
            client = NotionAPIClient(config.NOTION_TOKEN)
            
            # Obtener conteos de bases de datos
            databases = {
                "projects": config.get("NOTION_PROJECTS_DB", ""),
                "cxc": config.get("NOTION_CXC_DB", ""),
                "cxp": config.get("NOTION_CXP_DB", "")
            }
            
            metrics = {}
            calculations = {
                "total_pending": 0,
                "total_revenue": 0,
                "total_expenses": 0
            }
            
            for db_type, db_id in databases.items():
                if db_id:
                    try:
                        # Optimización: usar filtros para obtener solo lo necesario
                        query_params = self._build_optimized_query(db_type)
                        
                        all_results = self._get_all_pages(client, db_id, query_params)
                        metrics[db_type] = len(all_results)
                        
                        # Calcular montos usando función unificada
                        self._calculate_amounts(db_type, all_results, calculations)
                                    
                    except Exception as e:
                        self.monitoring.logger.error(f"Error obteniendo métricas de {db_type}: {e}")
                        metrics[db_type] = 0
            
            # Calcular totales finales
            metrics.update({
                "pending_amount": calculations["total_pending"],
                "total_revenue": calculations["total_revenue"],
                "total_expenses": calculations["total_expenses"],
                "net_profit": calculations["total_revenue"] - calculations["total_expenses"]
            })
            
            # Actualizar caché
            self._metrics_cache = metrics
            self._cache_timestamp = current_time
            self.monitoring.logger.info(f"Métricas actualizadas: {len(metrics)} campos")
            
            return metrics
            
        except Exception as e:
            self.monitoring.logger.error(f"Error crítico obteniendo métricas de Notion: {e}")
            return self._get_default_metrics()
    
    def _build_optimized_query(self, db_type):
        """Construir query optimizado según el tipo de base de datos"""
        base_query = {"page_size": 100}
        
        # Para CxC, solo necesitamos propiedades específicas
        if db_type == "cxc":
            base_query["filter"] = {
                "property": "Monto",
                "number": {
                    "is_not_empty": True
                }
            }
        
        return base_query
    
    def _get_all_pages(self, client, db_id, query_params, max_pages=10):
        """Obtener todas las páginas con límite de seguridad"""
        all_results = []
        start_cursor = None
        page_count = 0
        
        while page_count < max_pages:
            page_count += 1
            
            if start_cursor:
                query_params["start_cursor"] = start_cursor
                
            response = client.post(f"databases/{db_id}/query", query_params)
            
            if not response["success"]:
                self.monitoring.logger.warning(f"Error en página {page_count} de {db_id}")
                break
            
            data = response["data"]
            results = data.get("results", [])
            all_results.extend(results)
            
            if not data.get("has_more", False):
                break
                
            start_cursor = data.get("next_cursor")
        
        self.monitoring.logger.info(f"Obtenidos {len(all_results)} registros de {db_id} en {page_count} páginas")
        return all_results
    
    def _calculate_amounts(self, db_type, results, calculations):
        """Calcular montos de manera unificada"""
        for result in results:
            props = result.get("properties", {})
            amount = props.get("Monto", {}).get("number", 0)
            
            if db_type == "cxc":
                status = props.get("Estado", {}).get("select", {}).get("name", "")
                if status != "Pagada":
                    calculations["total_pending"] += amount
                calculations["total_revenue"] += amount
            
            elif db_type == "cxp":
                calculations["total_expenses"] += amount
    
    def _get_default_metrics(self):
        """Retornar métricas por defecto"""
        return {
            "projects": 0, "cxc": 0, "cxp": 0, 
            "pending_amount": 0, "total_revenue": 0, 
            "total_expenses": 0, "net_profit": 0
        }
    
    def get_recent_activity(self):
        """Obtener actividad reciente del sistema mejorada"""
        try:
            activities = []
            
            # Buscar logs más recientes dinámicamente
            log_pattern = "logs/erp_*.log"
            log_files = sorted(Path(".").glob(log_pattern), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if log_files:
                log_file = log_files[0]  # Log más reciente
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-50:]  # Más líneas para mejor contexto
                        
                    for line in lines:
                        timestamp = self._extract_timestamp_from_log(line) or datetime.now()
                        
                        if "Cuentas por Cobrar" in line and "generadas" in line:
                            activities.append({
                                "type": "cxc_generated",
                                "description": "Cuentas por Cobrar generadas",
                                "timestamp": timestamp.isoformat()
                            })
                        elif "Cuentas por Pagar" in line and "generadas" in line:
                            activities.append({
                                "type": "cxp_generated", 
                                "description": "Cuentas por Pagar generadas",
                                "timestamp": timestamp.isoformat()
                            })
                        elif "alerta" in line.lower():
                            activities.append({
                                "type": "alert_triggered",
                                "description": "Alerta activada",
                                "timestamp": timestamp.isoformat()
                            })
                        elif "métricas actualizadas" in line.lower():
                            activities.append({
                                "type": "metrics_updated",
                                "description": "Métricas del dashboard actualizadas",
                                "timestamp": timestamp.isoformat()
                            })
                            
                except Exception as e:
                    self.monitoring.logger.warning(f"Error leyendo archivo de log: {e}")
            
            # Agregar actividad de caché más informativa
            cache_stats = self.optimizer.cache_manager.get_stats()
            if cache_stats.get("hits", 0) > 0:
                hit_rate = (cache_stats.get("hits", 0) / 
                           (cache_stats.get("hits", 0) + cache_stats.get("misses", 1))) * 100
                activities.append({
                    "type": "cache_performance",
                    "description": f"Cache hit rate: {hit_rate:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Agregar actividad de métricas cacheadas
            if self._cache_timestamp:
                cache_age = datetime.now() - datetime.fromtimestamp(self._cache_timestamp)
                activities.append({
                    "type": "cache_status",
                    "description": f"Métricas cacheadas hace {cache_age.seconds}s",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Ordenar por timestamp y limitar
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:10]
            
        except Exception as e:
            self.monitoring.logger.error(f"Error obteniendo actividad reciente: {e}")
            return []
    
    def _extract_timestamp_from_log(self, line):
        """Extraer timestamp de línea de log"""
        try:
            # Buscar patrones comunes de timestamp en logs
            import re
            patterns = [
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except:
            pass
        return None
    
    def serve_dashboard(self):
        """Servir el archivo HTML del dashboard"""
        try:
            dashboard_path = Path("data/dashboards/dashboard.html")
            if dashboard_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.send_error(404, "Dashboard not found")
        except Exception as e:
            self.send_error(500, f"Error serving dashboard: {e}")
    
    def send_json_response(self, data):
        """Enviar respuesta JSON con headers mejorados"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Sobreescribir para reducir logs"""
        pass

def start_dashboard_server(port=8080):
    """Iniciar el servidor del dashboard"""
    try:
        server = HTTPServer(('localhost', port), DashboardAPI)
        print(f"🚀 Dashboard API server iniciado en http://localhost:{port}")
        print(f"📊 Dashboard disponible en http://localhost:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

if __name__ == "__main__":
    start_dashboard_server()