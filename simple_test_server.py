#!/usr/bin/env python3
"""
Servidor ultra simple para diagnosticar el dashboard
"""

import http.server
import socketserver
import json
import os
from datetime import datetime

PORT = 8083

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Request: {self.path}")
        
        if self.path == '/api/dashboard':
            # Respuesta simple con datos de prueba
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "projects_total": 5,
                    "cxc_total": 3,
                    "cxp_total": 2,
                    "pending_amount": 15000,
                    "total_revenue": 45000,
                    "total_expenses": 28000,
                    "net_profit": 17000,
                    "success_rate": 100,
                    "system_health": 100,
                    "api_calls": 0,
                    "api_response_time": 0.5,
                    "cache_hit_rate": 85
                },
                "alerts": [{
                    "level": "info",
                    "title": "Servidor de Prueba",
                    "message": "Funcionando correctamente",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "Servidor HTTP", "status": "active"},
                        {"name": "Dashboard", "status": "active"}
                    ]
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode())
            print("Datos de prueba enviados")
        else:
            # Servir archivos estáticos
            super().do_GET()
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def start_simple_server():
    try:
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            print(f"Servidor simple iniciado en http://localhost:{PORT}")
            print(f"Dashboard: http://localhost:{PORT}/data/dashboards/dashboard_standalone.html")
            print("Presiona Ctrl+C para detener")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_simple_server()