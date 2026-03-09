#!/usr/bin/env python3
"""
Servidor corregido para dashboard con Notion - sin emojis para Windows
"""

import http.server
import socketserver
import json
import requests
import os
import webbrowser
from datetime import datetime

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs de bases de datos (actualizados desde config)
CXP_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"  # Cuentas por Pagar
CXC_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"  # Cuentas por Cobrar
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"  # Centros de Costo

PORT = 8083

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/dashboard':
            self.handle_api_request()
        else:
            # Servir archivos estáticos
            super().do_GET()
    
    def handle_api_request(self):
        """Manejar solicitudes a la API con datos reales de Notion"""
        try:
            print("Obteniendo datos de Notion...")
            # Obtener datos de Notion
            metrics = self.get_notion_metrics()
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "alerts": [{
                    "level": "info",
                    "title": "Datos Actualizados",
                    "message": f"Conectado a {metrics['api_calls']} bases de datos",
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
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            print(f"Datos enviados: {len(response_data['metrics'])} métricas")
            
        except Exception as e:
            print(f"Error en API: {e}")
            # Enviar respuesta de error
            error_response = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
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
                }
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(error_response).encode())
    
    def get_notion_metrics(self):
        """Obtener métricas reales de Notion"""
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        
        metrics = {
            "projects_total": 0,
            "cxc_total": 0,
            "cxp_total": 0,
            "pending_amount": 0,
            "total_revenue": 0,
            "total_expenses": 0,
            "net_profit": 0,
            "success_rate": 100,
            "system_health": 100,
            "api_calls": 0,
            "api_response_time": 0.0,
            "cache_hit_rate": 0
        }
        
        try:
            # Consultar CxC
            print("Consultando CxC...")
            cxc_url = f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query"
            cxc_response = requests.post(cxc_url, headers=headers, json={"page_size": 50}, timeout=10)
            metrics["api_calls"] += 1
            
            if cxc_response.status_code == 200:
                cxc_data = cxc_response.json()
                cxc_results = cxc_data.get("results", [])
                metrics["cxc_total"] = len(cxc_results)
                print(f"CxC: {len(cxc_results)} registros encontrados")
                
                for result in cxc_results:
                    props = result.get("properties", {})
                    # Usar "Monto Base" que es el campo correcto en CxC
                    amount = props.get("Monto Base", {}).get("number", 0)
                    status = props.get("Estado", {}).get("select", {}).get("name", "")
                    if status and "pagada" not in status.lower():
                        metrics["pending_amount"] += amount
                    metrics["total_revenue"] += amount
            else:
                print(f"Error CxC: {cxc_response.status_code}")
                    
        except Exception as e:
            print(f"Error CxC: {e}")
        
        try:
            # Consultar CxP
            print("Consultando CxP...")
            cxp_url = f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query"
            cxp_response = requests.post(cxp_url, headers=headers, json={"page_size": 50}, timeout=10)
            metrics["api_calls"] += 1
            
            if cxp_response.status_code == 200:
                cxp_data = cxp_response.json()
                cxp_results = cxp_data.get("results", [])
                metrics["cxp_total"] = len(cxp_results)
                print(f"CxP: {len(cxp_results)} registros encontrados")
                
                for result in cxp_results:
                    props = result.get("properties", {})
                    # Usar "Monto" que es el campo correcto en CxP
                    amount = props.get("Monto", {}).get("number", 0)
                    metrics["total_expenses"] += amount
            else:
                print(f"Error CxP: {cxp_response.status_code}")
                    
        except Exception as e:
            print(f"Error CxP: {e}")
        
        try:
            # Consultar Proyectos
            print("Consultando Proyectos...")
            projects_url = f"{NOTION_BASE_URL}/databases/{CENTROS_DB_ID}/query"
            projects_response = requests.post(projects_url, headers=headers, json={"page_size": 50}, timeout=10)
            metrics["api_calls"] += 1
            
            if projects_response.status_code == 200:
                projects_data = projects_response.json()
                projects_results = projects_data.get("results", [])
                metrics["projects_total"] = len(projects_results)
                print(f"Proyectos: {len(projects_results)} registros encontrados")
            else:
                print(f"Error Proyectos: {projects_response.status_code}")
                
        except Exception as e:
            print(f"Error Proyectos: {e}")
        
        # Calcular beneficio neto
        metrics["net_profit"] = metrics["total_revenue"] - metrics["total_expenses"]
        
        print(f"Métricas finales: {metrics}")
        return metrics
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Reducir logs para mayor claridad"""
        pass

def start_server():
    """Iniciar servidor"""
    try:
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"Servidor dashboard iniciado en http://localhost:{PORT}")
            print(f"Dashboard: http://localhost:{PORT}/data/dashboards/dashboard_standalone.html")
            print("Presiona Ctrl+C para detener")
            
            # Abrir navegador
            try:
                webbrowser.open(f'http://localhost:{PORT}/data/dashboards/dashboard_standalone.html')
                print("[OK] Navegador abierto automáticamente")
            except:
                print("[WARN] No se pudo abrir el navegador automáticamente")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_server()
