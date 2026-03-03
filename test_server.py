#!/usr/bin/env python3
"""
Servidor simple para probar conexión con Notion
"""

import json
import sys
import os
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

class SimpleNotionHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        print(f"Petición GET recibida: {self.path}")
        
        if self.path == '/api/test':
            self.test_notion_connection()
        elif self.path == '/api/dashboard':
            self.handle_dashboard_request()
        elif self.path == '/':
            self.serve_dashboard()
        else:
            self.send_error(404, "Not Found")
    
    def test_notion_connection(self):
        """Probar conexión con Notion"""
        try:
            print("Probando conexión con Notion...")
            url = f"{NOTION_BASE_URL}/users/me"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "success": True,
                    "message": "Conexión exitosa con Notion",
                    "user": data.get("results", [{}])[0].get("name", "Unknown"),
                    "status": response.status_code
                }
            else:
                result = {
                    "success": False,
                    "message": f"Error en conexión: {response.status_code}",
                    "error": response.text
                }
            
            self.send_json_response(result)
            
        except Exception as e:
            print(f"Error en test_notion_connection: {e}")
            self.send_json_response({
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    def handle_dashboard_request(self):
        """Manejar petición del dashboard"""
        try:
            print("Obteniendo datos del dashboard...")
            
            # Datos de ejemplo
            response_data = {
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
                    "level": "info",
                    "title": "Sistema Iniciado",
                    "message": "Servidor funcionando correctamente",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "Servidor HTTP", "status": "active"},
                        {"name": "API Notion", "status": "testing"}
                    ]
                }
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            print(f"Error en handle_dashboard_request: {e}")
            self.send_error(500, f"Internal Server Error: {e}")
    
    def serve_dashboard(self):
        """Servir el dashboard HTML"""
        try:
            dashboard_path = "data/dashboards/dashboard_standalone.html"
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.wfile.write(content.encode('utf-8'))
                
        except Exception as e:
            print(f"Error sirviendo dashboard: {e}")
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
        print(f"LOG: {format % args}")

def start_test_server(port=8081):
    """Iniciar servidor de prueba"""
    try:
        server = HTTPServer(('localhost', port), SimpleNotionHandler)
        print(f"Servidor de prueba iniciado en http://localhost:{port}")
        print(f"Dashboard: http://localhost:{port}/")
        print(f"Test API: http://localhost:{port}/api/test")
        print("Presiona Ctrl+C para detener")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_test_server()
