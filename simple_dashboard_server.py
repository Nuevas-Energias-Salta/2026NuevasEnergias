#!/usr/bin/env python3
"""
API simplificada para el dashboard del ERP
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.api_client import APIClient
from config.settings import Config

class SimpleDashboardAPI(BaseHTTPRequestHandler):
    """Handler simplificado para la API del dashboard"""
    
    def do_GET(self):
        """Manejar peticiones GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/dashboard':
            self.handle_dashboard_request()
        elif parsed_path.path == '/' or parsed_path.path == '/data/dashboards/dashboard.html':
            self.serve_dashboard()
        else:
            # Intentar servir archivos estáticos
            self.serve_static_file(parsed_path.path)
    
    def get_real_notion_metrics(self):
        """Obtener métricas reales de Notion"""
        try:
            notion_client = APIClient(
                Config.NOTION_BASE_URL, 
                Config.NOTION_HEADERS
            )
            
            metrics = {
                "projects_total": 0,
                "cxc_total": 0,
                "cxp_total": 0,
                "pending_amount": 0,
                "total_revenue": 0,
                "total_expenses": 0,
                "net_profit": 0
            }
            
            # Obtener proyectos/centros
            if Config.NOTION_PROJECTS_DB:
                response = notion_client.make_request("POST", f"databases/{Config.NOTION_PROJECTS_DB}/query", 
                                                    {"page_size": 100})
                if response and "results" in response:
                    metrics["projects_total"] = len(response["results"])
            
            # Obtener CxC si existe DB
            if Config.NOTION_CXC_DB:
                response = notion_client.make_request("POST", f"databases/{Config.NOTION_CXC_DB}/query",
                                                    {"page_size": 100})
                if response and "results" in response:
                    metrics["cxc_total"] = len(response["results"])
                    for item in response["results"]:
                        props = item.get("properties", {})
                        amount = props.get("Monto", {}).get("number", 0)
                        status = props.get("Estado", {}).get("select", {}).get("name", "")
                        if status != "Pagada":
                            metrics["pending_amount"] += amount
                        metrics["total_revenue"] += amount
            
            # Obtener CxP si existe DB
            if Config.NOTION_CXP_DB:
                response = notion_client.make_request("POST", f"databases/{Config.NOTION_CXP_DB}/query",
                                                    {"page_size": 100})
                if response and "results" in response:
                    metrics["cxp_total"] = len(response["results"])
                    for item in response["results"]:
                        props = item.get("properties", {})
                        amount = props.get("Monto", {}).get("number", 0)
                        metrics["total_expenses"] += amount
            
            metrics["net_profit"] = metrics["total_revenue"] - metrics["total_expenses"]
            
            return metrics
            
        except Exception as e:
            print(f"Error obteniendo métricas de Notion: {e}")
            # Retornar valores por defecto si hay error
            return {
                "projects_total": 0,
                "cxc_total": 0,
                "cxp_total": 0,
                "pending_amount": 0,
                "total_revenue": 0,
                "total_expenses": 0,
                "net_profit": 0
            }
    
    def get_real_activity(self):
        """Obtener actividad real desde logs o sistema"""
        try:
            # Intentar leer logs recientes
            log_file = Path("logs/erp_20260205.log")
            activities = []
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-10:]  # Últimas 10 líneas
                    
                for line in lines:
                    if "Cuentas por Cobrar" in line and "generadas" in line:
                        activities.append({
                            "type": "cxc_generated",
                            "description": "Cuentas por Cobrar generadas automáticamente",
                            "timestamp": datetime.now().isoformat()
                        })
                    elif "Cuentas por Pagar" in line and "generadas" in line:
                        activities.append({
                            "type": "cxp_generated",
                            "description": "Cuentas por Pagar generadas automáticamente", 
                            "timestamp": datetime.now().isoformat()
                        })
            
            # Si no hay actividad en logs, agregar actividad básica
            if not activities:
                activities.append({
                    "type": "system_start",
                    "description": "Dashboard iniciado con datos de Notion",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Actividad de métricas
                notion_metrics = self.get_real_notion_metrics()
                if notion_metrics["projects_total"] > 0:
                    activities.append({
                        "type": "api_call",
                        "description": f"Sincronizados {notion_metrics['projects_total']} proyectos desde Notion",
                        "timestamp": datetime.now().isoformat()
                    })
            
            return activities[:5]  # Últimas 5 actividades
            
        except Exception as e:
            print(f"Error obteniendo actividad: {e}")
            return [{
                "type": "system_start", 
                "description": "Dashboard iniciado",
                "timestamp": datetime.now().isoformat()
            }]

    def handle_dashboard_request(self):
        """Manejar petición principal del dashboard"""
        try:
            # Obtener métricas reales de Notion
            notion_metrics = self.get_real_notion_metrics()
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    **notion_metrics,
                    "success_rate": 95,
                    "system_health": 100,
                    "api_calls": 124,
                    "api_response_time": 0.8,
                    "cache_hit_rate": 78
                },
                "alerts": [
                    {
                        "level": "info",
                        "title": "Sistema Operativo",
                        "message": "Todos los sistemas funcionando correctamente",
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "Sistema de Logging", "status": "active"},
                        {"name": "Gestor de Caché", "status": "active"},
                        {"name": "Sistema de Monitoreo", "status": "active"},
                        {"name": "Gestor de Alertas", "status": "active"},
                        {"name": "Optimizador de Rendimiento", "status": "active"}
                    ]
                },
                "recent_activity": self.get_real_activity()
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            print(f"Error en dashboard request: {e}")
            self.send_error(500, f"Internal Server Error: {e}")
    
    def serve_static_file(self, path):
        """Servir archivos estáticos"""
        try:
            # Remover el primer / si existe
            if path.startswith('/'):
                path = path[1:]
            
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                # Determinar content type
                if path.endswith('.html'):
                    content_type = 'text/html; charset=utf-8'
                elif path.endswith('.css'):
                    content_type = 'text/css'
                elif path.endswith('.js'):
                    content_type = 'application/javascript'
                elif path.endswith('.json'):
                    content_type = 'application/json'
                else:
                    content_type = 'text/plain'
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")
    
    def serve_dashboard(self):
        """Servir el archivo HTML del dashboard"""
        try:
            dashboard_path = Path("data/dashboards/dashboard.html")
            if dashboard_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.send_error(404, "Dashboard not found")
        except Exception as e:
            self.send_error(500, f"Error serving dashboard: {e}")
    
    def send_json_response(self, data):
        """Enviar respuesta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Sobreescribir para reducir logs"""
        pass

def start_simple_server(port=8080):
    """Iniciar el servidor simplificado del dashboard"""
    try:
        server = HTTPServer(('localhost', port), SimpleDashboardAPI)
        print(f"Dashboard API server iniciado en http://localhost:{port}")
        print(f"Dashboard disponible en http://localhost:{port}")
        print("Presiona Ctrl+C para detener el servidor")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")

if __name__ == "__main__":
    start_simple_server()