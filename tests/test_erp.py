#!/usr/bin/env python3
"""
Sistema de pruebas unitarias para Notion ERP
Pruebas básicas para componentes principales
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Agregar path para importar módulos del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.logger import ERPLogger, ErrorHandler
from src.utils.performance import CacheManager, PerformanceOptimizer
from src.utils.monitoring import MonitoringSystem, SystemMetrics
from src.utils.api_client import APIClient, NotionAPIClient, TrelloAPIClient
from config.settings import config

class TestLogger(unittest.TestCase):
    """Pruebas para el sistema de logging"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = ERPLogger("TEST", log_level="DEBUG")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Prueba creación de logger"""
        self.assertIsNotNone(self.logger.logger)
        self.assertEqual(self.logger.name, "TEST")
    
    def test_log_levels(self):
        """Prueba diferentes niveles de logging"""
        with self.assertNoLogs():
            self.logger.info("Test info message")
            self.logger.warning("Test warning message")
            self.logger.success("Test success message")
    
    def test_error_handling(self):
        """Prueba manejo de errores"""
        error_handler = ErrorHandler(self.logger)
        
        test_exception = ValueError("Test error")
        result = error_handler.handle_exception(test_exception, "test context")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unexpected_error")

class TestCacheManager(unittest.TestCase):
    """Pruebas para el gestor de caché"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir, default_ttl=60)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_set_get(self):
        """Prueba guardar y obtener del caché"""
        test_data = {"key": "value", "number": 123}
        
        # Guardar en caché
        result = self.cache_manager.set("test_key", test_data)
        self.assertTrue(result)
        
        # Obtener del caché
        cached_data = self.cache_manager.get("test_key")
        self.assertEqual(cached_data, test_data)
    
    def test_cache_expiration(self):
        """Prueba expiración de caché"""
        test_data = {"test": "data"}
        
        # Guardar con TTL muy corto
        self.cache_manager.set("test_key", test_data, ttl=1)
        
        # Debe estar disponible inmediatamente
        cached_data = self.cache_manager.get("test_key", ttl=1)
        self.assertEqual(cached_data, test_data)
        
        # Esperar expiración
        import time
        time.sleep(2)
        
        # No debería estar disponible
        cached_data = self.cache_manager.get("test_key", ttl=1)
        self.assertIsNone(cached_data)
    
    def test_cache_key_generation(self):
        """Prueba generación de claves de caché"""
        key1 = self.cache_manager._get_cache_key("test_string")
        key2 = self.cache_manager._get_cache_key({"a": 1, "b": 2})
        key3 = self.cache_manager._get_cache_key({"b": 2, "a": 1})  # Orden diferente
        
        self.assertEqual(key2, key3)  # Mismo contenido, misma clave
        self.assertNotEqual(key1, key2)
    
    def test_cache_stats(self):
        """Prueba estadísticas del caché"""
        test_data = {"test": "data"}
        
        # Operaciones para generar estadísticas
        self.cache_manager.set("test_key", test_data)
        self.cache_manager.get("test_key")
        self.cache_manager.get("non_existent_key")
        
        stats = self.cache_manager.get_stats()
        
        self.assertEqual(stats["stats"]["set"], 1)
        self.assertEqual(stats["stats"]["memory_hit"], 1)
        self.assertEqual(stats["stats"]["miss"], 1)
        self.assertGreater(stats["hit_rate"], 0)

class TestAPIClient(unittest.TestCase):
    """Pruebas para el cliente API"""
    
    def setUp(self):
        self.client = APIClient("https://httpbin.org", max_retries=2)
    
    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Prueba solicitud exitosa"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        result = self.client.get("/get")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], {"data": "test"})
        self.assertEqual(result["status_code"], 200)
    
    @patch('requests.Session.request')
    def test_api_error_handling(self, mock_request):
        """Prueba manejo de errores de API"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response
        
        result = self.client.get("/unauthorized")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "auth_error")
    
    @patch('requests.Session.request')
    def test_retry_mechanism(self, mock_request):
        """Prueba mecanismo de reintentos"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_request.return_value = mock_response
        
        result = self.client.get("/error")
        
        self.assertFalse(result["success"])
        # Debe haberse reintentado (llamadas > 1)
        self.assertGreater(mock_request.call_count, 1)

class TestNotionAPIClient(unittest.TestCase):
    """Pruebas para cliente Notion API"""
    
    def setUp(self):
        self.notion_client = NotionAPIClient("test_token")
    
    def test_headers_configuration(self):
        """Prueba configuración de headers"""
        self.assertIn("Authorization", self.notion_client.session.headers)
        self.assertIn("Notion-Version", self.notion_client.session.headers)
        self.assertEqual(self.notion_client.session.headers["Authorization"], "Bearer test_token")
    
    @patch.object(APIClient, 'post')
    def test_query_database(self, mock_post):
        """Prueba query de base de datos Notion"""
        mock_post.return_value = {
            "success": True,
            "data": {"results": [{"id": "test"}]}
        }
        
        result = self.notion_client.query_database("test_db_id")
        
        self.assertTrue(result["success"])
        mock_post.assert_called_once_with("databases/test_db_id/query", data={})

class TestTrelloAPIClient(unittest.TestCase):
    """Pruebas para cliente Trello API"""
    
    def setUp(self):
        self.trello_client = TrelloAPIClient("test_api_key", "test_token")
    
    def test_auth_params(self):
        """Prueba parámetros de autenticación"""
        self.assertEqual(self.trello_client.base_params["key"], "test_api_key")
        self.assertEqual(self.trello_client.base_params["token"], "test_token")
    
    @patch.object(APIClient, 'get')
    def test_get_boards(self, mock_get):
        """Prueba obtener boards de Trello"""
        mock_get.return_value = {
            "success": True,
            "data": [{"id": "board1", "name": "Test Board"}]
        }
        
        result = self.trello_client.get_boards()
        
        self.assertTrue(result["success"])
        mock_get.assert_called_once_with("members/me/boards", params=None)

class TestPerformanceOptimizer(unittest.TestCase):
    """Pruebas para optimizador de rendimiento"""
    
    def setUp(self):
        self.cache_manager = CacheManager(default_ttl=60)
        self.optimizer = PerformanceOptimizer(cache_manager=self.cache_manager)
    
    def test_cached_api_call_decorator(self):
        """Prueba decorador de caché para API calls"""
        call_count = 0
        
        @self.optimizer.cached_api_call(ttl=60)
        def test_function(param1, param2=None):
            nonlocal call_count
            call_count += 1
            return {"result": f"{param1}_{param2}", "call": call_count}
        
        # Primera llamada - debe ejecutar función
        result1 = test_function("test", param2="value")
        self.assertEqual(call_count, 1)
        
        # Segunda llamada con mismos parámetros - debe usar caché
        result2 = test_function("test", param2="value")
        self.assertEqual(call_count, 1)  # No incrementó
        self.assertEqual(result1, result2)
    
    def test_parallel_execution(self):
        """Prueba ejecución paralela"""
        def mock_task(task_id):
            import time
            time.sleep(0.1)
            return {"task_id": task_id, "processed": True}
        
        tasks = [{"task_id": i} for i in range(5)]
        results = self.optimizer.parallel_execution(tasks, mock_task)
        
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r["success"] for r in results))
    
    def test_batch_operation(self):
        """Prueba operaciones por lotes"""
        def mock_operation(item):
            return {"item": item, "processed": True}
        
        items = list(range(10))
        results = self.optimizer.batch_operation(items, mock_operation, batch_size=3)
        
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r["success"] for r in results))

class TestMonitoringSystem(unittest.TestCase):
    """Pruebas para sistema de monitoreo"""
    
    def setUp(self):
        self.monitoring = MonitoringSystem()
    
    def test_metrics_collection(self):
        """Prueba colección de métricas"""
        metrics = self.monitoring.collect_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertIsInstance(metrics.timestamp, datetime)
    
    def test_alert_creation(self):
        """Prueba creación de alertas"""
        self.monitoring.create_alert("warning", "Test Alert", "Test message")
        
        self.assertEqual(len(self.monitoring.alerts), 1)
        alert = self.monitoring.alerts[0]
        self.assertEqual(alert["level"], "warning")
        self.assertEqual(alert["title"], "Test Alert")
        self.assertEqual(alert["message"], "Test message")
    
    def test_dashboard_data(self):
        """Prueba generación de datos para dashboard"""
        # Agregar métricas de prueba
        test_metrics = SystemMetrics(
            timestamp=datetime.now(),
            total_projects=10,
            total_cxc=5,
            pending_amount=10000.0
        )
        self.monitoring.metrics_history.append(test_metrics)
        
        dashboard_data = self.monitoring.get_dashboard_data()
        
        self.assertIn("current_metrics", dashboard_data)
        self.assertIn("summary", dashboard_data)
        self.assertEqual(dashboard_data["summary"]["total_projects"], 10)

class TestConfigSettings(unittest.TestCase):
    """Pruebas para configuración"""
    
    def test_config_validation(self):
        """Prueba validación de configuración"""
        # Mockear variables de entorno
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'TRELLO_API_KEY': 'test_key',
            'TRELLO_TOKEN': 'test_trello_token'
        }):
            from config.settings import Config
            result = Config.validate_config()
            self.assertTrue(result)
    
    def test_config_missing_tokens(self):
        """Prueba detección de tokens faltantes"""
        with patch.dict(os.environ, {}, clear=True):
            from config.settings import Config
            result = Config.validate_config()
            self.assertFalse(result)

def run_all_tests():
    """Ejecuta todas las pruebas"""
    # Crear suite de pruebas
    test_classes = [
        TestLogger,
        TestCacheManager,
        TestAPIClient,
        TestNotionAPIClient,
        TestTrelloAPIClient,
        TestPerformanceOptimizer,
        TestMonitoringSystem,
        TestConfigSettings
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generar reporte
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
        "success": result.wasSuccessful()
    }
    
    # Guardar reporte
    Path("tests/results").mkdir(exist_ok=True)
    with open("tests/results/test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n🧪 Test Report:")
    print(f"   Tests ejecutados: {report['tests_run']}")
    print(f"   Fallos: {report['failures']}")
    print(f"   Errores: {report['errors']}")
    print(f"   Tasa de éxito: {report['success_rate']:.1%}")
    print(f"   Estado: {'✅ Éxito' if report['success'] else '❌ Falló'}")
    
    return report

if __name__ == "__main__":
    print("🚀 Iniciando pruebas unitarias de Notion ERP...")
    report = run_all_tests()
    
    if report["success"]:
        print("\n✅ Todas las pruebas pasaron exitosamente")
    else:
        print("\n❌ Algunas pruebas fallaron - revisa el reporte detallado")