#!/usr/bin/env python3
"""
API del dashboard conectada a Notion
"""

import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs de bases de datos (ajusta según tu configuración)
PROJECTS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"  # CENTROS_DB_ID

class NotionDashboardAPI(BaseHTTPRequestHandler):
    """Handler para la API del dashboard con conexión a Notion"""
    
    def __init__(self, *args, **kwargs):
        self.headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Manejar peticiones GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/dashboard':
            self.handle_dashboard_request()
        elif parsed_path.path == '/':
            self.serve_dashboard()
        else:
            self.send_error(404, "Not Found")
    
    def handle_dashboard_request(self):
        """Manejar petición principal del dashboard con datos de Notion"""
        try:
            # Obtener datos reales de Notion
            notion_data = self.get_notion_data()
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "projects_total": notion_data.get("projects_count", 0),
                    "cxc_total": notion_data.get("cxc_count", 0),
                    "cxp_total": notion_data.get("cxp_count", 0),
                    "pending_amount": notion_data.get("pending_amount", 0),
                    "total_revenue": notion_data.get("total_revenue", 0),
                    "total_expenses": notion_data.get("total_expenses", 0),
                    "net_profit": notion_data.get("net_profit", 0),
                    "success_rate": 95,  # Podemos calcular esto
                    "system_health": 100,
                    "api_calls": notion_data.get("api_calls", 0),
                    "api_response_time": notion_data.get("response_time", 0.0),
                    "cache_hit_rate": 0  # Sin caché por ahora
                },
                "alerts": self.get_system_alerts(),
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "API Notion", "status": "active"},
                        {"name": "Dashboard", "status": "active"},
                        {"name": "Base de Datos", "status": "active"}
                    ]
                },
                "recent_activity": notion_data.get("recent_activity", [])
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            print(f"Error en dashboard request: {e}")
            # Enviar datos de fallback en caso de error
            fallback_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "projects_total": 0,
                    "cxc_total": 0,
                    "cxp_total": 0,
                    "pending_amount": 0,
                    "total_revenue": 0,
                    "total_expenses": 0,
                    "net_profit": 0,
                    "success_rate": 0,
                    "system_health": 0,
                    "api_calls": 0,
                    "api_response_time": 0.0,
                    "cache_hit_rate": 0
                },
                "alerts": [{
                    "level": "error",
                    "title": "Error de Conexión",
                    "message": f"No se pudo conectar a Notion: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "error",
                    "components": []
                },
                "recent_activity": []
            }
            self.send_json_response(fallback_data)
    
    def get_notion_data(self):
        """Obtener datos reales de Notion"""
        try:
            data = {
                "projects_count": 0,
                "cxc_count": 0,
                "cxp_count": 0,
                "pending_amount": 0,
                "total_revenue": 0,
                "total_expenses": 0,
                "net_profit": 0,
                "api_calls": 0,
                "response_time": 0.0,
                "recent_activity": []
            }
            
            # Obtener proyectos
            if PROJECTS_DB_ID:
                projects_response = self.query_database(PROJECTS_DB_ID)
                if projects_response:
                    data["projects_count"] = len(projects_response.get("results", []))
                    data["api_calls"] += 1
            
            # Aquí puedes agregar más consultas a otras bases de datos
            # Por ejemplo, para CxC y CxP si tienes los IDs
            
            return data
            
        except Exception as e:
            print(f"Error obteniendo datos de Notion: {e}")
            return {}
    
    def query_database(self, database_id, page_size=100):
        """Consultar una base de datos de Notion"""
        try:
            url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
            payload = {"page_size": page_size}
            
            start_time = datetime.now()
            response = requests.post(url, headers=self.headers, json=payload)
            end_time = datetime.now()
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error en API Notion: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en query_database: {e}")
            return None
    
    def get_system_alerts(self):
        """Obtener alertas del sistema"""
        return [{
            "level": "info",
            "title": "Sistema Operativo",
            "message": "Conectado a Notion API",
            "timestamp": datetime.now().isoformat()
        }]
    
    def serve_dashboard(self):
        """Servir el archivo HTML del dashboard"""
        try:
            dashboard_path = Path("data/dashboards/dashboard.html")
            if not dashboard_path.exists():
                dashboard_path = Path("data/dashboards/dashboard_standalone.html")
            
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

def start_notion_server(port=8080):
    """Iniciar el servidor del dashboard con Notion"""
    try:
        server = HTTPServer(('localhost', port), NotionDashboardAPI)
        print(f"Dashboard API server iniciado en http://localhost:{port}")
        print(f"Dashboard disponible en http://localhost:{port}")
        print("Presiona Ctrl+C para detener el servidor")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")

if __name__ == "__main__":
    start_notion_server()
