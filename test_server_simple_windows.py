#!/usr/bin/env python3
"""
Servidor de prueba simple para verificar el dashboard - sin emojis
"""

import http.server
import socketserver
import os
import webbrowser
from datetime import datetime
import json

PORT = 8083

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Request received: {self.path}")
        
        if self.path == '/api/dashboard':
            # Respuesta de prueba para la API
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
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
                    "api_calls": 5,
                    "api_response_time": 0.5,
                    "cache_hit_rate": 85
                },
                "alerts": [{
                    "level": "info",
                    "title": "Sistema Operativo",
                    "message": "Todos los sistemas funcionando correctamente",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "API Notion", "status": "active"},
                        {"name": "Dashboard", "status": "active"}
                    ]
                }
            }
            
            self.wfile.write(json.dumps(response_data).encode())
        else:
            # Servir archivos estáticos
            super().do_GET()
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        super().end_headers()

def start_test_server():
    try:
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        
        with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
            print(f"Servidor de prueba iniciado en http://localhost:{PORT}")
            print(f"Dashboard: http://localhost:{PORT}/data/dashboards/dashboard_standalone.html")
            print("Presiona Ctrl+C para detener")
            
            # Verificar si el archivo del dashboard existe
            dashboard_path = "data/dashboards/dashboard_standalone.html"
            if os.path.exists(dashboard_path):
                print(f"[OK] Dashboard encontrado en: {dashboard_path}")
                # Abrir navegador automáticamente
                try:
                    webbrowser.open(f'http://localhost:{PORT}/data/dashboards/dashboard_standalone.html')
                    print("[OK] Navegador abierto automáticamente")
                except:
                    print("[WARN] No se pudo abrir el navegador automáticamente")
                    print(f"   Abre manualmente: http://localhost:{PORT}/data/dashboards/dashboard_standalone.html")
            else:
                print(f"[ERROR] Dashboard NO encontrado en: {dashboard_path}")
                print("   Verifica que el archivo exista")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_test_server()