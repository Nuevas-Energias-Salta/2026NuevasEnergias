#!/usr/bin/env python3
"""
Servidor dashboard corregido con IDs y campos correctos
"""

import http.server
import socketserver
import json
import requests
import os
import webbrowser
from datetime import datetime

# Configuración con IDs CORRECTOS
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs CORRECTOS de bases de datos financieras
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"  # Cuentas por Cobrar
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"  # Cuentas por Pagar
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"  # Centros de Costo

PORT = 8083

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Request: {self.path}")
        
        if self.path == '/api/dashboard':
            self.handle_api_request()
        else:
            # Servir archivos estáticos
            super().do_GET()
    
    def handle_api_request(self):
        """Manejar solicitudes a la API con datos CORRECTOS de Notion"""
        try:
            print("Obteniendo datos CORRECTOS de Notion...")
            metrics = self.get_notion_metrics_correct()
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "alerts": [{
                    "level": "info",
                    "title": "Datos Actualizados (CORREGIDO)",
                    "message": f"Conectado a {metrics['api_calls']} bases de datos CORRECTAS",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "API Notion", "status": "active"},
                        {"name": "Dashboard", "status": "active"},
                        {"name": "Base CxC", "status": "active"},
                        {"name": "Base CxP", "status": "active"}
                    ]
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            print(f"Datos CORRECTOS enviados: {metrics}")
            
        except Exception as e:
            print(f"Error en API: {e}")
            self.send_error(500, str(e))
    
    def get_notion_metrics_correct(self):
        """Obtener métricas CORRECTAS de Notion con campos adecuados"""
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
            # Consultar CxC CORRECTA
            print("Consultando CxC CORRECTA...")
            cxc_url = f"{NOTION_BASE_URL}/databases/{CXC_DB_ID}/query"
            cxc_response = requests.post(cxc_url, headers=headers, json={"page_size": 100}, timeout=10)
            metrics["api_calls"] += 1
            
            if cxc_response.status_code == 200:
                cxc_data = cxc_response.json()
                cxc_results = cxc_data.get("results", [])
                metrics["cxc_total"] = len(cxc_results)
                print(f"CxC CORRECTA: {len(cxc_results)} registros encontrados")
                
                # Analizar estructura de CxC
                if cxc_results:
                    sample = cxc_results[0]
                    props = sample.get("properties", {})
                    print(f"Campos CxC: {list(props.keys())[:5]}...")  # Mostrar primeros 5 campos
                    
                    # Buscar campos de monto en CxC
                    cxc_amount_fields = []
                    for field_name in props.keys():
                        if 'monto' in field_name.lower() or 'amount' in field_name.lower() or 'importe' in field_name.lower():
                            cxc_amount_fields.append(field_name)
                    
                    print(f"Campos de monto CxC: {cxc_amount_fields}")
                    
                    # Calcular montos (usar el primer campo de monto encontrado)
                    for result in cxc_results:
                        props = result.get("properties", {})
                        
                        # Intentar diferentes campos de monto
                        amount = 0
                        for field in cxc_amount_fields:
                            field_data = props.get(field, {})
                            if field_data.get("type") == "number":
                                amount = field_data.get("number", 0)
                                break
                        
                        # Buscar estado
                        status = ""
                        status_fields = [k for k in props.keys() if 'estado' in k.lower() or 'status' in k.lower()]
                        for field in status_fields:
                            field_data = props.get(field, {})
                            if field_data.get("type") == "select":
                                status = field_data.get("select", {}).get("name", "")
                                break
                        
                        # Sumar al total
                        metrics["total_revenue"] += amount
                        
                        # Sumar a pendientes si no está pagado
                        if status and "pagada" not in status.lower():
                            metrics["pending_amount"] += amount
            else:
                print(f"Error CxC: {cxc_response.status_code}")
                    
        except Exception as e:
            print(f"Error CxC: {e}")
        
        try:
            # Consultar CxP CORRECTA
            print("Consultando CxP CORRECTA...")
            cxp_url = f"{NOTION_BASE_URL}/databases/{CXP_DB_ID}/query"
            cxp_response = requests.post(cxp_url, headers=headers, json={"page_size": 100}, timeout=10)
            metrics["api_calls"] += 1
            
            if cxp_response.status_code == 200:
                cxp_data = cxp_response.json()
                cxp_results = cxp_data.get("results", [])
                metrics["cxp_total"] = len(cxp_results)
                print(f"CxP CORRECTA: {len(cxp_results)} registros encontrados")
                
                # Analizar estructura de CxP
                if cxp_results:
                    sample = cxp_results[0]
                    props = sample.get("properties", {})
                    print(f"Campos CxP: {list(props.keys())[:5]}...")  # Mostrar primeros 5 campos
                    
                    # Para CxP, el campo principal es "Monto"
                    for result in cxp_results:
                        props = result.get("properties", {})
                        
                        # Usar campo "Monto" principal
                        amount = props.get("Monto", {}).get("number", 0)
                        metrics["total_expenses"] += amount
            else:
                print(f"Error CxP: {cxp_response.status_code}")
                    
        except Exception as e:
            print(f"Error CxP: {e}")
        
        try:
            # Consultar Proyectos/Centros
            print("Consultando Centros...")
            projects_url = f"{NOTION_BASE_URL}/databases/{CENTROS_DB_ID}/query"
            projects_response = requests.post(projects_url, headers=headers, json={"page_size": 100}, timeout=10)
            metrics["api_calls"] += 1
            
            if projects_response.status_code == 200:
                projects_data = projects_response.json()
                projects_results = projects_data.get("results", [])
                metrics["projects_total"] = len(projects_results)
                print(f"Centros: {len(projects_results)} registros encontrados")
            else:
                print(f"Error Centros: {projects_response.status_code}")
                
        except Exception as e:
            print(f"Error Centros: {e}")
        
        # Calcular beneficio neto
        metrics["net_profit"] = metrics["total_revenue"] - metrics["total_expenses"]
        
        print(f"Métricas finales CORRECTAS: {metrics}")
        return metrics
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Reducir logs para mayor claridad"""
        pass

def start_server():
    """Iniciar servidor corregido"""
    try:
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"Servidor dashboard CORREGIDO iniciado en http://localhost:{PORT}")
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
