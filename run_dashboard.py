#!/usr/bin/env python3
"""
Servidor HTTP ultra-simple para el dashboard
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8080

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

def start_server():
    """Iniciar servidor HTTP simple"""
    try:
        # Cambiar al directorio del proyecto
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        
        # Crear servidor
        with socketserver.TCPServer(("", PORT), DashboardHTTPRequestHandler) as httpd:
            print(f"Servidor iniciado en http://localhost:{PORT}")
            print(f"Dashboard disponible en http://localhost:{PORT}/data/dashboards/dashboard.html")
            print("Presiona Ctrl+C para detener")
            
            # Abrir navegador
            webbrowser.open(f'http://localhost:{PORT}/data/dashboards/dashboard.html')
            
            # Iniciar servidor
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_server()