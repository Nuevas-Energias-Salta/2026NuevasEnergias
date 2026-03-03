#!/usr/bin/env python3
"""
Script principal mejorado del sistema Notion ERP
Integra todas las mejoras: logging, monitoreo, optimización, alertas, etc.
"""

import sys
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar sistemas mejorados
from src.utils.logger import get_logger, log_function_call
from src.utils.monitoring import get_monitoring_system
from src.utils.performance import get_performance_optimizer, get_db_optimizer
from src.utils.alerts import get_alert_manager, create_info_alert
from src.utils.integrations import get_integrations_manager
from config.settings import config

class EnhancedERPSystem:
    """Sistema ERP mejorado con todas las funcionalidades"""
    
    def __init__(self):
        self.logger = get_logger("ERP_MAIN")
        self.monitoring = get_monitoring_system()
        self.optimizer = get_performance_optimizer()
        self.db_optimizer = get_db_optimizer()
        self.alert_manager = get_alert_manager()
        self.integrations = get_integrations_manager()
        
        self.start_time = datetime.now()
        
    def startup(self):
        """Inicialización del sistema"""
        self.logger.script_start("Enhanced ERP System")
        
        # Validar configuración
        if not config.validate_config():
            self.logger.error("❌ Configuración inválida - revisa tus tokens")
            return False
        
        # Iniciar sistemas
        self.monitoring.start_monitoring(interval_seconds=60)
        self.alert_manager.start_automated_monitoring(interval_seconds=60)
        
        # Mensaje de bienvenida
        create_info_alert(
            "Sistema ERP Iniciado",
            "🚀 El sistema Notion ERP ha sido iniciado con todas las mejoras activadas",
            data={
                "components": ["Logging", "Monitoreo", "Performance", "Alertas", "Integraciones"],
                "start_time": self.start_time.isoformat()
            }
        )
        
        self.logger.success("✅ Sistema ERP iniciado exitosamente")
        return True
    
    def shutdown(self):
        """Apagado graceful del sistema"""
        self.logger.info("🛑 Iniciando apagado del sistema...")
        
        # Detener monitoreo
        self.monitoring.stop_monitoring()
        self.alert_manager.stop_automated_monitoring()
        
        # Guardar estado final
        self.monitoring.save_dashboard()
        self.alert_manager.save_alerts()
        
        # Generar reporte final
        duration = datetime.now() - self.start_time
        self.logger.script_end("Enhanced ERP System", {
            "duration": str(duration),
            "alerts_generated": len(self.alert_manager.alerts),
            "cache_hit_rate": self.optimizer.cache_manager.get_stats().get("hit_rate", 0)
        })
        
        print("\n🎉 Sistema ERP detenido exitosamente")
        print("📊 Revisa los archivos generados:")
        print("   📈 Dashboard: data/dashboards/dashboard.html")
        print("   🚨 Alertas: data/alerts/current_alerts.json")
        print("   📋 Logs: logs/erp_*.log")
    
    @log_function_call("generate_accounts_enhanced")
    def generate_accounts(self):
        """Generación mejorada de cuentas con todas las optimizaciones"""
        self.logger.info("🏗️ Iniciando generación mejorada de cuentas...")
        
        try:
            # Importar scripts originales
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'notion'))
            import auto_generate_cxc_improved
            import auto_generate_cxp
            
            # Ejecutar con optimización
            start_time = time.time()
            
            # CxC con caché
            self.logger.info("💰 Generando Cuentas por Cobrar...")
            cxc_result = auto_generate_cxc_improved.main()
            
            # CxP con caché
            self.logger.info("💸 Generando Cuentas por Pagar...")
            cxp_result = auto_generate_cxp.main()
            
            total_time = time.time() - start_time
            
            # Métricas
            stats = {
                "cxc_generated": cxc_result if isinstance(cxc_result, int) else 0,
                "cxp_generated": cxp_result if isinstance(cxp_result, int) else 0,
                "execution_time": total_time
            }
            
            self.logger.success(f"✅ Cuentas generadas en {total_time:.2f}s", stats)
            
            # Notificación
            if self.integrations.slack:
                self.integrations.slack.send_report({
                    "title": "📊 Generación de Cuentas Completada",
                    "metrics": {
                        "CxC Generadas": stats["cxc_generated"],
                        "CxP Generadas": stats["cxp_generated"],
                        "Tiempo Ejecución": f"{total_time:.2f}s"
                    }
                })
            
            return True
            
        except Exception as e:
            self.logger.error("Error en generación de cuentas", e)
            return False
    
    def run_health_check(self):
        """Ejecuta check de salud del sistema"""
        self.logger.info("🏥 Ejecutando health check del sistema...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # Check de configuración
        try:
            config_valid = config.validate_config()
            health_status["components"]["config"] = "ok" if config_valid else "error"
            if not config_valid:
                health_status["issues"].append("Configuración inválida")
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["config"] = "error"
            health_status["issues"].append(f"Error config: {e}")
            health_status["status"] = "degraded"
        
        # Check de APIs
        try:
            from src.utils.api_client import NotionAPIClient
            client = NotionAPIClient(config.NOTION_TOKEN)
            test_response = client.get("users/me")
            health_status["components"]["notion_api"] = "ok" if test_response["success"] else "error"
            if not test_response["success"]:
                health_status["issues"].append("Notion API no responde")
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["notion_api"] = "error"
            health_status["issues"].append(f"Error Notion API: {e}")
            health_status["status"] = "degraded"
        
        # Check de caché
        cache_stats = self.optimizer.cache_manager.get_stats()
        health_status["components"]["cache"] = "ok"
        health_status["cache_stats"] = cache_stats
        
        # Check de alertas
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.level.value == "critical"]
        health_status["components"]["alerts"] = "ok"
        health_status["active_alerts"] = len(active_alerts)
        health_status["critical_alerts"] = len(critical_alerts)
        
        if critical_alerts:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Hay {len(critical_alerts)} alertas críticas")
        
        # Guardar health check
        Path("data/health").mkdir(exist_ok=True)
        with open("data/health/health_status.json", "w") as f:
            import json
            json.dump(health_status, f, indent=2)
        
        # Reporte (sin emojis para evitar errores Unicode)
        status_symbols = {"healthy": "[OK]", "degraded": "[!]", "unhealthy": "[X]"}
        print(f"\n{status_symbols[health_status['status']]} Health Status: {health_status['status'].upper()}")
        
        for component, status in health_status["components"].items():
            symbol = "[OK]" if status == "ok" else "[X]"
            print(f"   {symbol} {component}: {status}")
        
        if health_status["issues"]:
            print("\n[!] Issues detectados:")
            for issue in health_status["issues"]:
                print(f"   - {issue}")
        
        return health_status
    
    def interactive_menu(self):
        """Menú interactivo mejorado"""
        while True:
            print("\n" + "="*70)
            print("🚀 NOTION ERP - SISTEMA MEJORADO")
            print("="*70)
            print("📊 Estado actual:")
            print(f"   • Alertas activas: {len(self.alert_manager.get_active_alerts())}")
            print(f"   • Cache hit rate: {self.optimizer.cache_manager.get_stats().get('hit_rate', 0):.1%}")
            print(f"   • Tiempo activo: {datetime.now() - self.start_time}")
            print("\n🎯 Opciones:")
            print("1. 🏗️  Generar Cuentas (CxC y CxP)")
            print("2. 🏥 Health Check del Sistema")
            print("3. 📊 Ver Dashboard")
            print("4. 🚨 Ver Alertas Activas")
            print("5. ⚡ Performance Report")
            print("6. 🧹 Limpiar Caché")
            print("7. 🔄 Evaluar Reglas de Alerta")
            print("8. 📈 Exportar Métricas")
            print("9. ❌ Salir")
            print("-"*70)
            
            choice = input("Selecciona una opción: ").strip()
            
            if choice == "1":
                self.generate_accounts()
            elif choice == "2":
                self.run_health_check()
            elif choice == "3":
                self.monitoring.save_dashboard()
                dashboard_path = Path("data/dashboards/dashboard.html").absolute()
                print(f"📊 Dashboard disponible en: {dashboard_path}")
                print("🌐 Abriendo en navegador...")
                import webbrowser
                webbrowser.open(f"file://{dashboard_path}")
            elif choice == "4":
                alerts = self.alert_manager.get_active_alerts()
                if alerts:
                    print(f"\n🚨 {len(alerts)} alertas activas:")
                    for alert in alerts[:10]:  # Mostrar últimas 10
                        level_symbols = {"info": "[i]", "warning": "[!]", "error": "[X]", "critical": "[!!]"}
                        symbol = level_symbols.get(alert.level.value, "[?]")
                        print(f"   {symbol} [{alert.level.value.upper()}] {alert.title}")
                        print(f"      {alert.message}")
                else:
                    print("✅ No hay alertas activas")
            elif choice == "5":
                report = self.optimizer.get_performance_report()
                print("\n⚡ Performance Report:")
                for func_name, metrics in report.get("function_metrics", {}).items():
                    print(f"   📈 {func_name}:")
                    print(f"      Calls: {metrics['total_calls']}")
                    print(f"      Avg time: {metrics['avg_time']:.3f}s")
                    print(f"      Total time: {metrics['total_time']:.3f}s")
            elif choice == "6":
                self.optimizer.cache_manager.clear()
                print("🧹 Caché limpiado exitosamente")
            elif choice == "7":
                metrics = self.monitoring.get_dashboard_data().get("current_metrics", {})
                self.alert_manager.evaluate_rules(metrics)
                print("🔄 Reglas de alerta evaluadas")
            elif choice == "8":
                metrics = self.monitoring.get_dashboard_data()
                with open("data/export/metrics_export.json", "w") as f:
                    import json
                    json.dump(metrics, f, indent=2)
                print("📈 Métricas exportadas a data/export/metrics_export.json")
            elif choice == "9":
                break
            else:
                print("❌ Opción inválida")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Notion ERP Sistema Mejorado")
    parser.add_argument("--mode", choices=["interactive", "generate", "health", "monitor"], 
                       default="interactive", help="Modo de ejecución")
    parser.add_argument("--config", help="Archivo de configuración alternativo")
    
    args = parser.parse_args()
    
    # Inicializar sistema
    erp = EnhancedERPSystem()
    
    try:
        if not erp.startup():
            return 1
        
        if args.mode == "interactive":
            erp.interactive_menu()
        elif args.mode == "generate":
            erp.generate_accounts()
        elif args.mode == "health":
            erp.run_health_check()
        elif args.mode == "monitor":
            print("📊 Modo monitorización activa (Ctrl+C para detener)")
            try:
                while True:
                    time.sleep(60)
                    erp.run_health_check()
            except KeyboardInterrupt:
                print("\n👋 Monitorización detenida")
        
    except KeyboardInterrupt:
        print("\n👋 Interrumpido por usuario")
    except Exception as e:
        erp.logger.error("Error fatal en sistema", e)
        return 1
    finally:
        erp.shutdown()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())