#!/usr/bin/env python3
"""
Servidor V2 para dashboard con Notion
- IDs Correctos de Bases Financieras
- Desglose Detallado: Total, Cobrado/Pagado, Pendiente
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

# IDs CORRECTOS (Verificados)
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"  # Cuentas por Cobrar (Ingresos)
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"  # Cuentas por Pagar (Egresos)
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"  # Centros de Costo (CATEGORÍAS FINANCIERAS)
PROYECTOS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"  # Proyectos / Obras

PORT = 8086
USD_EXCHANGE_RATE = 1420

# Caché Simple
_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 300 # 5 minutos
}

class DashboardHandler_V2(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/dashboard':
            self.handle_api_request()
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(302)
            self.send_header('Location', '/data/dashboards/dashboard_standalone.html')
            self.end_headers()
        else:
            super().do_GET()
    
    def handle_api_request(self):
        try:
            global _cache
            now = datetime.now()
            
            # Verificar caché
            if (_cache["data"] and _cache["timestamp"] and 
                (now - _cache["timestamp"]).total_seconds() < _cache["ttl"]):
                print("Usando datos desde caché...")
                metrics = _cache["data"]
            else:
                print("Obteniendo datos financieros V2 (Notion API)...")
                metrics = self.get_financial_metrics_v2()
            
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "alerts": [{
                    "level": "info",
                    "title": "Datos Financieros Actualizados",
                    "message": f"Desglose completo cargado exitosamente",
                    "timestamp": datetime.now().isoformat()
                }],
                "system_status": {
                    "status": "operational",
                    "components": [
                        {"name": "API Notion V2", "status": "active"},
                        {"name": "Dashboard V2", "status": "active"}
                    ]
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            print(f"Error V2: {e}")
            self.send_error(500, str(e))

    def get_financial_metrics_v2(self):
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        
        # Estructura de métricas expandida
        metrics = {
            # Ingresos (CxC)
            "income_total": 0,      # Total Facturado
            "income_collected": 0,  # Ya Cobrado
            "income_pending": 0,    # Por Cobrar
            "cxc_count": 0,         # Cantidad de facturas
            
            # Egresos (CxP)
            "expenses_total": 0,    # Total Gastos
            "expenses_paid": 0,     # Ya Pagado (ARS)
            "expenses_pending": 0,  # Por Pagar (ARS)
            "expenses_total_usd": 0,    # Total Gastos USD
            "expenses_paid_usd": 0,     # Ya Pagado USD
            "expenses_pending_usd": 0,  # Por Pagar USD
            "cxp_count": 0,         # Cantidad de comprobantes
            
            # Globales
            "net_profit": 0,        # Beneficio Neto (Cobrado - Pagado)
            "projected_profit": 0,  # Beneficio Proyectado (Total - Total)
            
            # Otros
            "projects_total": 0,
            "cost_centers": {}, # Desglose por centro de costo
            "api_calls": 0,
            "success_rate": 100,
            "system_health": 100
        }
        
        # 0. Pre-cargar Mapa de Centros de Costo
        try:
            # Query filtrada para traer solo los activos
            filter_payload = {
                "filter": {
                    "property": "Activo",
                    "checkbox": {
                        "equals": True
                    }
                }
            }
            cc_results = self.fetch_all_results(CENTROS_DB_ID, headers, filter_payload)
            metrics["api_calls"] += 1
            
            for p in cc_results:
                p_id = p["id"]
                p_props = p.get("properties", {})
                title_list = p_props.get("Nombre", {}).get("title", [])
                p_name = title_list[0].get("plain_text", "Sin Nombre") if title_list else "Sin Nombre"
                
                # Omitir si no tiene nombre o es vacío
                if p_name == "Sin Nombre" or not p_name.strip():
                    continue

                metrics["cost_centers"][p_id] = {
                    "name": p_name,
                    "income": 0,
                    "expenses": 0,
                    "expenses_usd": 0,
                    "balance": 0
                }
            print(f"Centros de Costo reales cargados: {len(metrics['cost_centers'])}")
        except Exception as e:
            print(f"Error cargando centros de costo: {e}")

        # 0.1 Obtener contador de proyectos reales (Proyectos/Obras)
        try:
            proj_results = self.fetch_all_results(PROYECTOS_DB_ID, headers)
            metrics["projects_total"] = len(proj_results)
            metrics["api_calls"] += 1
        except Exception as e:
            print(f"Error cargando proyectos: {e}")
            metrics["projects_total"] = 0
        
        # 1. Procesar INGRESOS (CxC)
        try:
            cxc_results = self.fetch_all_results(CXC_DB_ID, headers)
            metrics["api_calls"] += 1
            metrics["cxc_count"] = len(cxc_results)
            print(f"CxC (Ingresos): {len(cxc_results)} registros")
            
            for item in cxc_results:
                props = item.get("properties", {})
                
                # Monto: "Monto Base" (number)
                amount = props.get("Monto Base", {}).get("number", 0) or 0
                
                # Estado: "Estado" (select)
                status_obj = props.get("Estado", {}).get("select", {})
                status = status_obj.get("name", "").lower() if status_obj else ""
                
                # Acumuladores globales
                metrics["income_total"] += amount
                
                # Acumulador por Centro de Costo
                cc_relations = props.get("Centro de Costo", {}).get("relation", [])
                if cc_relations:
                    cc_id = cc_relations[0].get("id")
                    if cc_id in metrics["cost_centers"]:
                        metrics["cost_centers"][cc_id]["income"] += amount

                if "cobrado" in status or "pagada" in status:
                    metrics["income_collected"] += amount
                else:
                    metrics["income_pending"] += amount
                    
        except Exception as e:
            print(f"Error procesando CxC: {e}")

        # 2. Procesar EGRESOS (CxP)
        try:
            cxp_results = self.fetch_all_results(CXP_DB_ID, headers)
            metrics["api_calls"] += 1
            metrics["cxp_count"] = len(cxp_results)
            print(f"CxP (Egresos): {len(cxp_results)} registros")
            
            for item in cxp_results:
                props = item.get("properties", {})
                
                # Monto: "Monto" (number) -> ARS
                amount_ars = props.get("Monto", {}).get("number", 0) or 0
                
                # Monto Dolares: "Monto Dolares" (number) -> USD
                amount_usd = props.get("Monto Dolares", {}).get("number", 0) or 0
                
                # Estado: "Estado" (select)
                status_obj = props.get("Estado", {}).get("select", {})
                status = status_obj.get("name", "").lower() if status_obj else ""
                is_paid = "pagado" in status or "abonado" in status

                # Acumulador por Centro de Costo
                cc_relations = props.get("Centro de Costo", {}).get("relation", [])
                if cc_relations:
                    cc_id = cc_relations[0].get("id")
                    if cc_id in metrics["cost_centers"]:
                        if amount_usd > 0:
                            metrics["cost_centers"][cc_id]["expenses_usd"] += amount_usd
                            # Convertimos a ARS para el balance del CC
                            metrics["cost_centers"][cc_id]["expenses"] += (amount_usd * USD_EXCHANGE_RATE)
                        else:
                            metrics["cost_centers"][cc_id]["expenses"] += amount_ars

                # --- Acumuladores Globales ---
                
                # Obtener valores de pago y saldo (según inspección/usuario)
                paid_val = props.get("Monto pagado", {}).get("number", 0) or 0
                
                # Saldo Pendiente (formula)
                saldo_prop = props.get("Saldo Pendiente", {})
                pending_val = 0
                if saldo_prop.get("type") == "formula":
                    f_val = saldo_prop.get("formula", {})
                    if f_val.get("type") == "number":
                        pending_val = f_val.get("number", 0) or 0
                elif saldo_prop.get("type") == "number":
                    pending_val = saldo_prop.get("number", 0) or 0

                # CASO USD: Si tiene "Monto Dolares" > 0, es un gasto en Dólares.
                if amount_usd > 0:
                    metrics["expenses_total_usd"] += amount_usd
                    metrics["expenses_paid_usd"] += paid_val
                    metrics["expenses_pending_usd"] += pending_val
                
                # CASO ARS: Si NO tiene "Monto Dolares" (o es 0), es en Pesos.
                else:
                    metrics["expenses_total"] += amount_ars
                    metrics["expenses_paid"] += paid_val
                    metrics["expenses_pending"] += pending_val
                    
        except Exception as e:
            print(f"Error procesando CxP: {e}")

        # 3. Calcular balances por centro de costo
        for cc_id in metrics["cost_centers"]:
            cc = metrics["cost_centers"][cc_id]
            cc["balance"] = cc["income"] - cc["expenses"]

        # 4. Cálculos finales
        # El beneficio neto real considera lo cobrado en ARS menos lo pagado en ARS (incluyendo conversiones si las hay)
        # Nota: Paid_val ya viene en la moneda correspondiente según el bucle de CxP
        # Vamos a unificar net_profit para que incluya USD convertidos
        expenses_paid_total_ars = metrics["expenses_paid"] + (metrics["expenses_paid_usd"] * USD_EXCHANGE_RATE)
        metrics["net_profit"] = metrics["income_collected"] - expenses_paid_total_ars
        
        income_total_ars = metrics["income_total"] # CxC asume ARS por defecto según inspección
        expenses_total_combined_ars = metrics["expenses_total"] + (metrics["expenses_total_usd"] * USD_EXCHANGE_RATE)
        metrics["projected_profit"] = income_total_ars - expenses_total_combined_ars
        
        # Guardar en caché
        global _cache
        _cache["data"] = metrics
        _cache["timestamp"] = datetime.now()
        
        return metrics

    def fetch_all_results(self, db_id, headers, filter_payload=None):
        """Helper para traer paginación completa si es necesario"""
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            payload = {"page_size": 100}
            if filter_payload:
                payload.update(filter_payload)
            if next_cursor:
                payload["start_cursor"] = next_cursor
                
            response = requests.post(
                f"{NOTION_BASE_URL}/databases/{db_id}/query",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"Error fetch DB {db_id}: {response.status_code}")
                break
                
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
            
        return all_results

def start_server():
    """Iniciar servidor V2"""
    try:
        os.chdir('C:/Users/Gonza/Desktop/Notion-project')
        print(f"--- SERVIDOR DASHBOARD V2 ---")
        print(f"Puerto: {PORT}")
        print(f"URL: http://localhost:{PORT}/data/dashboards/dashboard_standalone.html")
        
        with socketserver.TCPServer(("", PORT), DashboardHandler_V2) as httpd:
            # Intentar abrir navegador
            try:
                webbrowser.open(f'http://localhost:{PORT}/data/dashboards/dashboard_standalone.html')
            except:
                pass
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error fatal: {e}")

if __name__ == "__main__":
    start_server()

