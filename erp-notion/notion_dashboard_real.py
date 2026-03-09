#!/usr/bin/env python3
"""
Dashboard con conexión real a Notion
"""

import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import io
from urllib.parse import urlparse

# Configuración
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs de bases de datos (CORREGIDOS)
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410" # Transactions
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a" # Transactions
CENTROS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f" # Proyectos/Obras

class NotionDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open("dashboard.log", "a") as f:
             f.write(f"{datetime.now()} - Request: {self.path}\n")
        print(f"Request: {self.path}")
        
        if self.path == '/api/dashboard':
            self.handle_dashboard_request()
        elif self.path == '/':
            self.serve_dashboard()
        else:
            self.send_error(404, "Not Found")
    
    def handle_dashboard_request(self):
        """Obtener datos reales de Notion"""
        try:
            headers = {
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": NOTION_VERSION
            }
            
            # Obtener datos de cada base de datos
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
            
            # Helper para paginación
            def fetch_all_results(db_id, label="DB"):
                results = []
                has_more = True
                next_cursor = None
                
                print(f" Consultando {label} (DB: {db_id})...")
                
                while has_more:
                    payload = {"page_size": 100}
                    if next_cursor:
                        payload["start_cursor"] = next_cursor
                        
                    try:
                        url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
                        response = requests.post(url, headers=headers, json=payload)
                        metrics["api_calls"] += 1
                        
                        if response.status_code == 200:
                            data = response.json()
                            batch = data.get("results", [])
                            results.extend(batch)
                            has_more = data.get("has_more", False)
                            next_cursor = data.get("next_cursor")
                            with open("dashboard.log", "a") as f:
                                f.write(f"{datetime.now()} - Batch {label}: {len(batch)} items\n")
                            print(f"   Batch recibido: {len(batch)} items. Total hasta ahora: {len(results)}")
                        else:
                            print(f"   Error en batch {label}: {response.status_code}")
                            has_more = False
                    except Exception as e:
                        with open("dashboard.log", "a") as f:
                             f.write(f"{datetime.now()} - EXCEPCION {label}: {e}\n")
                        print(f"   Excepcion consultando {label}: {e}")
                        has_more = False
                
                return results

            # Consultar CxC
            try:
                cxc_results = fetch_all_results(CXC_DB_ID, "CxC")
                metrics["cxc_total"] = len(cxc_results)
                
                # Calcular montos pendientes
                for result in cxc_results:
                    props = result.get("properties", {})
                    
                    # CORRECCION: Usar "Monto Base" para CxC
                    amount = 0
                    if "Monto Base" in props and "number" in props["Monto Base"]:
                        amount = props["Monto Base"]["number"] or 0
                        
                    # Estado
                    status = ""
                    if "Estado" in props and "select" in props["Estado"] and props["Estado"]["select"]:
                        status = props["Estado"]["select"]["name"]
                    
                    if status and status.lower() not in ["pagada", "cobrada", "pagado", "cobrado"]:
                        metrics["pending_amount"] += amount
                    metrics["total_revenue"] += amount
                
                print(f"   CxC Total: {metrics['cxc_total']} | Ingresos: ${metrics['total_revenue']:,.2f} | Pendiente: ${metrics['pending_amount']:,.2f}")
                    
            except Exception as e:
                print(f"Error procesando CxC: {e}")

            # Consultar CxP
            try:
                cxp_results = fetch_all_results(CXP_DB_ID, "CxP")
                metrics["cxp_total"] = len(cxp_results)
                
                # Calcular total de gastos
                for result in cxp_results:
                    props = result.get("properties", {})
                    # Monto: En CxP se llama "Monto"
                    amount = 0
                    if "Monto" in props and "number" in props["Monto"]:
                        amount = props["Monto"]["number"] or 0
                    metrics["total_expenses"] += amount
                
                print(f"   CxP Total: {metrics['cxp_total']} | Total Gastos: ${metrics['total_expenses']:,.2f}")
                    
            except Exception as e:
                print(f"Error procesando CxP: {e}")
            
            # Consultar Proyectos/Centros
            try:
                projects_results = fetch_all_results(CENTROS_DB_ID, "Proyectos")
                metrics["projects_total"] = len(projects_results)
                print(f"   Proyectos Total: {metrics['projects_total']}")
                    
            except Exception as e:
                print(f"Error procesando Proyectos: {e}")
            
            # Calcular beneficio neto
            metrics["net_profit"] = metrics["total_revenue"] - metrics["total_expenses"]
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "alerts": [{
                    "level": "info",
                    "title": "Sistema Conectado",
                    "message": f"Datos actualizados desde {metrics['api_calls']} bases de datos",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "API Notion", "status": "active"},
                        {"name": "Base CxC", "status": "active"},
                        {"name": "Base CxP", "status": "active"},
                        {"name": "Base Proyectos", "status": "active"}
                    ]
                }
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            with open("dashboard.log", "a") as f:
                 f.write(f"{datetime.now()} - ERROR GLOBAL: {e}\n")
            print(f"Error en dashboard request: {e}")
            self.send_error(500, f"Internal Server Error: {e}")
    
    def serve_dashboard(self):
        """Servir dashboard HTML"""
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

def start_notion_dashboard(port=8080):
    """Iniciar dashboard con Notion"""
    try:
        server = HTTPServer(('localhost', port), NotionDashboardHandler)
        print(f"Dashboard Notion iniciado en http://localhost:{port}")
        print(f"Dashboard: http://localhost:{port}/")
        print("Presiona Ctrl+C para detener")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_notion_dashboard()
