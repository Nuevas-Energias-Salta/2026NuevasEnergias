#!/usr/bin/env python3
"""
Script de diagnóstico unificado para conexiones API Notion y Dashboard
Versión sin emojis para compatibilidad con Windows
"""

import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from src.utils.api_client import NotionAPIClient

class DiagnosticTool:
    """Herramienta de diagnóstico completa"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
    
    def add_test_result(self, test_name: str, status: str, details: str = "", data: dict = None):
        """Agregar resultado de prueba"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "WARN"
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            result["data"] = data
        
        self.results["tests"].append(result)
        
        if status == "FAIL":
            self.results["errors"].append(f"{test_name}: {details}")
        elif status == "WARN":
            self.results["warnings"].append(f"{test_name}: {details}")
    
    def test_notion_connection(self):
        """Probar conexión básica con Notion API"""
        try:
            print("Probando conexión con Notion API...")
            
            headers = config.get_notion_headers()
            user_url = f"{config.NOTION_BASE_URL}/users/me"
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                user_name = user_data.get("results", [{}])[0].get("name", "Unknown")
                self.add_test_result(
                    "Conexión Notion API", 
                    "PASS", 
                    f"Conectado como: {user_name}",
                    {"user": user_name, "status_code": response.status_code}
                )
                return True
            else:
                self.add_test_result(
                    "Conexión Notion API", 
                    "FAIL", 
                    f"Error HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.add_test_result("Conexión Notion API", "FAIL", f"Excepción: {str(e)}")
            return False
    
    def test_database_access(self):
        """Probar acceso a bases de datos configuradas"""
        print("Probando acceso a bases de datos...")
        
        databases = {
            "Proyectos/Centros": config.NOTION_PROJECTS_DB,
            "Cuentas por Cobrar": config.NOTION_CXC_DB,
            "Cuentas por Pagar": config.NOTION_CXP_DB
        }
        
        client = NotionAPIClient(config.NOTION_TOKEN)
        success_count = 0
        
        for db_name, db_id in databases.items():
            if not db_id:
                self.add_test_result(
                    f"BD {db_name}", 
                    "WARN", 
                    "ID no configurado"
                )
                continue
            
            try:
                response = client.query_database(db_id, page_size=1)
                if response["success"]:
                    results = response["data"].get("results", [])
                    self.add_test_result(
                        f"BD {db_name}", 
                        "PASS", 
                        f"Acceso correcto, {len(results)} registros encontrados",
                        {"db_id": db_id, "record_count": len(results)}
                    )
                    success_count += 1
                else:
                    self.add_test_result(
                        f"BD {db_name}", 
                        "FAIL", 
                        f"Error en API: {response.get('message', 'Unknown error')}"
                    )
                    
            except Exception as e:
                self.add_test_result(f"BD {db_name}", "FAIL", f"Excepción: {str(e)}")
        
        return success_count == len([db for db in databases.values() if db])
    
    def test_data_consistency(self):
        """Probar consistencia de datos y campos"""
        print("Probando consistencia de datos...")
        
        try:
            client = NotionAPIClient(config.NOTION_TOKEN)
            
            # Probar CxC si está configurada
            if config.NOTION_CXC_DB:
                response = client.query_database(config.NOTION_CXC_DB, page_size=5)
                if response["success"]:
                    results = response["data"].get("results", [])
                    if results:
                        # Verificar campos esperados
                        sample = results[0]
                        props = sample.get("properties", {})
                        
                        expected_fields = ["Monto", "Estado", "Cliente"]
                        found_fields = []
                        missing_fields = []
                        
                        for field in expected_fields:
                            if field in props:
                                found_fields.append(field)
                            else:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            self.add_test_result(
                                "Campos CxC", 
                                "WARN", 
                                f"Campos faltantes: {', '.join(missing_fields)}",
                                {"found": found_fields, "missing": missing_fields}
                            )
                        else:
                            self.add_test_result(
                                "Campos CxC", 
                                "PASS", 
                                f"Todos los campos presentes: {', '.join(found_fields)}"
                            )
            
            # Probar CxP si está configurada
            if config.NOTION_CXP_DB:
                response = client.query_database(config.NOTION_CXP_DB, page_size=5)
                if response["success"]:
                    results = response["data"].get("results", [])
                    if results:
                        sample = results[0]
                        props = sample.get("properties", {})
                        
                        expected_fields = ["Monto", "Estado", "Proveedor"]
                        found_fields = []
                        missing_fields = []
                        
                        for field in expected_fields:
                            if field in props:
                                found_fields.append(field)
                            else:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            self.add_test_result(
                                "Campos CxP", 
                                "WARN", 
                                f"Campos faltantes: {', '.join(missing_fields)}",
                                {"found": found_fields, "missing": missing_fields}
                            )
                        else:
                            self.add_test_result(
                                "Campos CxP", 
                                "PASS", 
                                f"Todos los campos presentes: {', '.join(found_fields)}"
                            )
            
            return True
            
        except Exception as e:
            self.add_test_result("Consistencia de Datos", "FAIL", f"Excepción: {str(e)}")
            return False
    
    def test_dashboard_servers(self):
        """Probar servidores de dashboard"""
        print("Probando servidores de dashboard...")
        
        server_files = [
            "simple_dashboard_server.py",
            "notion_dashboard_real.py", 
            "simple_notion_server.py"
        ]
        
        for server_file in server_files:
            server_path = Path(server_file)
            if server_path.exists():
                self.add_test_result(
                    f"Archivo {server_file}", 
                    "PASS", 
                    "Servidor encontrado"
                )
            else:
                self.add_test_result(
                    f"Archivo {server_file}", 
                    "WARN", 
                    "Servidor no encontrado"
                )
        
        # Verificar archivos HTML del dashboard
        dashboard_files = [
            "data/dashboards/dashboard.html",
            "data/dashboards/dashboard_standalone.html"
        ]
        
        for dashboard_file in dashboard_files:
            dashboard_path = Path(dashboard_file)
            if dashboard_path.exists():
                self.add_test_result(
                    f"Dashboard {dashboard_file}", 
                    "PASS", 
                    "Archivo HTML encontrado"
                )
            else:
                self.add_test_result(
                    f"Dashboard {dashboard_file}", 
                    "FAIL", 
                    "Archivo HTML no encontrado"
                )
    
    def test_configuration(self):
        """Probar configuración del sistema"""
        print("Probando configuración del sistema...")
        
        # Verificar token
        if config.NOTION_TOKEN:
            if config.NOTION_TOKEN.startswith("ntn_"):
                self.add_test_result("Token Notion", "PASS", "Token parece válido")
            else:
                self.add_test_result("Token Notion", "WARN", "Token tiene formato inusual")
        else:
            self.add_test_result("Token Notion", "FAIL", "Token no configurado")
        
        # Verificar URLs
        if config.NOTION_BASE_URL:
            self.add_test_result("URL Notion", "PASS", f"URL configurada: {config.NOTION_BASE_URL}")
        else:
            self.add_test_result("URL Notion", "FAIL", "URL no configurada")
        
        # Verificar IDs de bases de datos
        db_configs = {
            "NOTION_PROJECTS_DB": config.NOTION_PROJECTS_DB,
            "NOTION_CXC_DB": config.NOTION_CXC_DB,
            "NOTION_CXP_DB": config.NOTION_CXP_DB
        }
        
        for db_name, db_id in db_configs.items():
            if db_id:
                self.add_test_result(f"Config {db_name}", "PASS", f"ID configurado: {db_id[:8]}...")
            else:
                self.add_test_result(f"Config {db_name}", "WARN", "ID no configurado")
    
    def generate_recommendations(self):
        """Generar recomendaciones basadas en resultados"""
        recommendations = []
        
        # Contar errores y advertencias
        error_count = len(self.results["errors"])
        warning_count = len(self.results["warnings"])
        
        if error_count > 0:
            recommendations.append("Corregir errores críticos antes de continuar")
        
        if warning_count > 0:
            recommendations.append("Revisar advertencias para mejorar funcionamiento")
        
        # Recomendaciones específicas
        failed_tests = [t for t in self.results["tests"] if t["status"] == "FAIL"]
        
        for test in failed_tests:
            if "Conexión Notion API" in test["test"]:
                recommendations.append("Verificar token de Notion y conexión a internet")
            elif "BD" in test["test"]:
                recommendations.append("Verificar IDs de bases de datos y permisos")
            elif "Dashboard" in test["test"]:
                recommendations.append("Asegurar que los archivos del dashboard existan")
        
        if not failed_tests and warning_count == 0:
            recommendations.append("Sistema funcionando correctamente")
        
        self.results["recommendations"] = recommendations
    
    def run_full_diagnostic(self):
        """Ejecutar diagnóstico completo"""
        print("Iniciando diagnóstico completo del sistema...")
        print("=" * 50)
        
        # Ejecutar todas las pruebas
        self.test_configuration()
        self.test_notion_connection()
        self.test_database_access()
        self.test_data_consistency()
        self.test_dashboard_servers()
        
        # Generar recomendaciones
        self.generate_recommendations()
        
        # Mostrar resumen
        self.print_summary()
        
        # Guardar resultados
        self.save_results()
    
    def print_summary(self):
        """Imprimir resumen de resultados"""
        print("\n" + "=" * 50)
        print("RESUMEN DEL DIAGNÓSTICO")
        print("=" * 50)
        
        total_tests = len(self.results["tests"])
        passed_tests = len([t for t in self.results["tests"] if t["status"] == "PASS"])
        failed_tests = len([t for t in self.results["tests"] if t["status"] == "FAIL"])
        warned_tests = len([t for t in self.results["tests"] if t["status"] == "WARN"])
        
        print(f"Total de pruebas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {failed_tests}")
        print(f"Advertencias: {warned_tests}")
        
        if failed_tests == 0:
            print("\n[OK] Todas las pruebas críticas pasaron!")
        else:
            print(f"\n[ERROR] {failed_tests} pruebas fallidas requieren atención")
        
        # Mostrar recomendaciones
        print("\nRECOMENDACIONES:")
        for rec in self.results["recommendations"]:
            print(f"   - {rec}")
    
    def save_results(self):
        """Guardar resultados en archivo JSON"""
        try:
            results_file = f"diagnostic_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\nResultados guardados en: {results_file}")
        except Exception as e:
            print(f"\nError guardando resultados: {e}")

if __name__ == "__main__":
    diagnostic = DiagnosticTool()
    diagnostic.run_full_diagnostic()

