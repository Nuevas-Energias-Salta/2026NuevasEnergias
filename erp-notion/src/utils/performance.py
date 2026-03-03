#!/usr/bin/env python3
"""
Sistema de optimización y caché para Notion ERP
Mejora el rendimiento de las operaciones repetitivas
"""

import json
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import asyncio
from collections import defaultdict

from .logger import get_logger, get_error_handler
from .api_client import APIClient

class CacheManager:
    """Gestor de caché inteligente"""
    
    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_stats = defaultdict(int)
        self.logger = get_logger("CACHE")
        self.lock = threading.RLock()
    
    def _get_cache_key(self, key_data: Union[str, Dict]) -> str:
        """Genera clave de caché única"""
        if isinstance(key_data, str):
            return key_data
        
        # Para diccionarios, crear hash consistente
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_file: Path, ttl: int) -> bool:
        """Verifica si el caché es válido"""
        if not cache_file.exists():
            return False
        
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < ttl
    
    def set(self, key: Union[str, Dict], value: Any, ttl: int = None) -> bool:
        """Guarda valor en caché"""
        try:
            cache_key = self._get_cache_key(key)
            ttl = ttl or self.default_ttl
            
            # Caché en memoria
            with self.lock:
                self.memory_cache[cache_key] = {
                    "value": value,
                    "expires_at": time.time() + ttl
                }
            
            # Caché en disco
            cache_file = self.cache_dir / f"{cache_key}.cache"
            cache_data = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.cache_stats["set"] += 1
            return True
            
        except Exception as e:
            self.logger.error("Error guardando en caché", e)
            return False
    
    def get(self, key: Union[str, Dict], ttl: int = None) -> Any:
        """Obtiene valor del caché"""
        try:
            cache_key = self._get_cache_key(key)
            ttl = ttl or self.default_ttl
            
            # Verificar caché en memoria primero
            with self.lock:
                if cache_key in self.memory_cache:
                    cache_entry = self.memory_cache[cache_key]
                    if time.time() < cache_entry["expires_at"]:
                        self.cache_stats["memory_hit"] += 1
                        return cache_entry["value"]
                    else:
                        del self.memory_cache[cache_key]
            
            # Verificar caché en disco
            cache_file = self.cache_dir / f"{cache_key}.cache"
            
            if self._is_cache_valid(cache_file, ttl):
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Restaurar a memoria caché
                with self.lock:
                    self.memory_cache[cache_key] = {
                        "value": cache_data["value"],
                        "expires_at": cache_data["expires_at"]
                    }
                
                self.cache_stats["disk_hit"] += 1
                return cache_data["value"]
            
            self.cache_stats["miss"] += 1
            return None
            
        except Exception as e:
            self.logger.error("Error leyendo caché", e)
            return None
    
    def delete(self, key: Union[str, Dict]) -> bool:
        """Elimina entrada del caché"""
        try:
            cache_key = self._get_cache_key(key)
            
            # Eliminar de memoria
            with self.lock:
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
            
            # Eliminar de disco
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if cache_file.exists():
                cache_file.unlink()
            
            self.cache_stats["delete"] += 1
            return True
            
        except Exception as e:
            self.logger.error("Error eliminando caché", e)
            return False
    
    def clear(self, pattern: str = None) -> bool:
        """Limpia caché (opcionalmente por patrón)"""
        try:
            if pattern:
                # Eliminar archivos que coincidan con patrón
                for cache_file in self.cache_dir.glob(f"*{pattern}*.cache"):
                    cache_file.unlink()
            else:
                # Limpiar todo
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
            
            # Limpiar caché en memoria
            with self.lock:
                if pattern:
                    keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                else:
                    self.memory_cache.clear()
            
            self.cache_stats["clear"] += 1
            return True
            
        except Exception as e:
            self.logger.error("Error limpiando caché", e)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        with self.lock:
            total_requests = (self.cache_stats["memory_hit"] + 
                             self.cache_stats["disk_hit"] + 
                             self.cache_stats["miss"])
            
            hit_rate = 0
            if total_requests > 0:
                hit_rate = (self.cache_stats["memory_hit"] + 
                           self.cache_stats["disk_hit"]) / total_requests
            
            return {
                "memory_cache_size": len(self.memory_cache),
                "disk_cache_files": len(list(self.cache_dir.glob("*.cache"))),
                "stats": dict(self.cache_stats),
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }

class PerformanceOptimizer:
    """Optimizador de rendimiento para operaciones"""
    
    def __init__(self, max_workers: int = 4, cache_manager: CacheManager = None):
        self.max_workers = max_workers
        self.cache_manager = cache_manager or CacheManager()
        self.logger = get_logger("PERFORMANCE")
        self.error_handler = get_error_handler()
        self.performance_metrics = defaultdict(list)
    
    def cached_api_call(self, ttl: int = 300, cache_key_prefix: str = "api"):
        """Decorador para cachear llamadas a API"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generar clave de caché
                cache_key = {
                    "prefix": cache_key_prefix,
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Intentar obtener del caché
                cached_result = self.cache_manager.get(cache_key, ttl)
                if cached_result is not None:
                    self.logger.debug(f"Cache hit para {func.__name__}")
                    return cached_result
                
                # Ejecutar función si no está en caché
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Guardar en caché
                self.cache_manager.set(cache_key, result, ttl)
                
                # Registrar métrica
                self.performance_metrics[func.__name__].append(execution_time)
                
                self.logger.debug(f"Ejecutado {func.__name__} en {execution_time:.2f}s")
                return result
                
            return wrapper
        return decorator
    
    def parallel_execution(self, tasks: List[Dict], 
                          task_func: Callable) -> List[Dict]:
        """Ejecuta tareas en paralelo"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_task = {
                executor.submit(task_func, **task): task 
                for task in tasks
            }
            
            # Recopilar resultados
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append({"task": task, "result": result, "success": True})
                except Exception as e:
                    error_result = self.error_handler.handle_exception(
                        e, f"tarea paralela: {task}"
                    )
                    results.append({
                        "task": task, 
                        "result": error_result, 
                        "success": False
                    })
        
        return results
    
    def batch_operation(self, items: List[Any], 
                       operation: Callable, 
                       batch_size: int = 10) -> List[Dict]:
        """Ejecuta operaciones por lotes"""
        results = []
        total_items = len(items)
        
        self.logger.info(f"🔄 Procesando {total_items} items en lotes de {batch_size}")
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_start_time = time.time()
            
            try:
                batch_results = []
                for item in batch:
                    start_time = time.time()
                    result = operation(item)
                    execution_time = time.time() - start_time
                    
                    batch_results.append({
                        "item": item,
                        "result": result,
                        "execution_time": execution_time,
                        "success": True
                    })
                
                batch_time = time.time() - batch_start_time
                self.logger.info(
                    f"✅ Lote {i//batch_size + 1} completado en {batch_time:.2f}s "
                    f"({len(batch)} items)"
                )
                
                results.extend(batch_results)
                
            except Exception as e:
                self.logger.error(f"Error en lote {i//batch_size + 1}", e)
                for item in batch:
                    results.append({
                        "item": item,
                        "result": None,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    def optimize_notion_queries(self, queries: List[Dict]) -> Dict:
        """Optimiza múltiples queries a Notion"""
        # Agrupar queries por database_id para reducir llamadas
        grouped_queries = defaultdict(list)
        for query in queries:
            db_id = query.get("database_id")
            if db_id:
                grouped_queries[db_id].append(query)
        
        results = {}
        
        for db_id, db_queries in grouped_queries.items():
            cache_key = f"notion_query_{db_id}"
            
            # Intentar obtener del caché
            cached_data = self.cache_manager.get(cache_key, ttl=60)  # 1 minuto TTL
            
            if cached_data:
                self.logger.debug(f"Cache hit para queries de {db_id}")
                results[db_id] = cached_data
            else:
                # Ejecutar query y guardar en caché
                try:
                    from .api_client import NotionAPIClient
                    from config.settings import config
                    
                    client = NotionAPIClient(config.NOTION_TOKEN)
                    
                    # Combinar filtros si es posible
                    combined_filter = None
                    for query in db_queries:
                        query_filter = query.get("filter")
                        if query_filter:
                            if combined_filter is None:
                                combined_filter = query_filter
                            else:
                                combined_filter = {
                                    "and": [combined_filter, query_filter]
                                }
                    
                    query_data = {}
                    if combined_filter:
                        query_data["filter"] = combined_filter
                    
                    response = client.query_database(db_id, **query_data)
                    
                    if response["success"]:
                        results[db_id] = response["data"]
                        self.cache_manager.set(cache_key, response["data"], ttl=60)
                        self.logger.debug(f"Query ejecutado y cacheado para {db_id}")
                    else:
                        results[db_id] = {"error": response.get("error")}
                
                except Exception as e:
                    self.logger.error(f"Error ejecutando queries para {db_id}", e)
                    results[db_id] = {"error": str(e)}
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte de rendimiento"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "cache_stats": self.cache_manager.get_stats(),
            "function_metrics": {}
        }
        
        # Estadísticas de funciones
        for func_name, times in self.performance_metrics.items():
            if times:
                report["function_metrics"][func_name] = {
                    "total_calls": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_time": sum(times)
                }
        
        return report
    
    def clear_performance_metrics(self):
        """Limpia métricas de rendimiento"""
        self.performance_metrics.clear()
        self.logger.info("🧹 Métricas de rendimiento limpiadas")

class DatabaseOptimizer:
    """Optimizador para operaciones de base de datos"""
    
    def __init__(self, cache_manager: CacheManager = None):
        self.cache_manager = cache_manager or CacheManager()
        self.logger = get_logger("DB_OPTIMIZER")
    
    def smart_query_notion(self, database_id: str, filters: Dict = None,
                         sort: List[Dict] = None, use_cache: bool = True) -> Dict:
        """Query optimizado para Notion con caché inteligente"""
        cache_key = {
            "database_id": database_id,
            "filters": filters,
            "sort": sort
        }
        
        if use_cache:
            cached_result = self.cache_manager.get(cache_key, ttl=300)  # 5 minutos
            if cached_result:
                self.logger.debug(f"Cache hit para query de {database_id}")
                return {"success": True, "data": cached_result, "from_cache": True}
        
        try:
            from .api_client import NotionAPIClient
            from config.settings import config
            
            client = NotionAPIClient(config.NOTION_TOKEN)
            
            query_data = {}
            if filters:
                query_data["filter"] = filters
            if sort:
                query_data["sorts"] = sort
            
            response = client.query_database(database_id, **query_data)
            
            if response["success"] and use_cache:
                self.cache_manager.set(cache_key, response["data"], ttl=300)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error en smart query para {database_id}", e)
            return {"success": False, "error": str(e)}
    
    def bulk_update_notion(self, updates: List[Dict]) -> Dict:
        """Actualización masiva optimizada"""
        start_time = time.time()
        successful_updates = []
        failed_updates = []
        
        self.logger.info(f"🔄 Iniciando actualización masiva de {len(updates)} items")
        
        # Procesar en lotes para evitar rate limits
        batch_size = 5  # Conservador para evitar límites
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            try:
                from .api_client import NotionAPIClient
                from config.settings import config
                
                client = NotionAPIClient(config.NOTION_TOKEN)
                
                for update in batch:
                    page_id = update.get("page_id")
                    properties = update.get("properties")
                    
                    if page_id and properties:
                        response = client.update_page(page_id, properties)
                        if response["success"]:
                            successful_updates.append(update)
                        else:
                            failed_updates.append({
                                "update": update,
                                "error": response.get("error")
                            })
                
                # Pequeña pausa entre lotes
                if i + batch_size < len(updates):
                    time.sleep(0.5)
            
            except Exception as e:
                self.logger.error(f"Error en lote de actualización", e)
                failed_updates.extend([{"update": u, "error": str(e)} for u in batch])
        
        total_time = time.time() - start_time
        
        result = {
            "success": True,
            "total_updates": len(updates),
            "successful_updates": len(successful_updates),
            "failed_updates": len(failed_updates),
            "execution_time": total_time,
            "success_rate": len(successful_updates) / len(updates) if updates else 0
        }
        
        self.logger.success(
            f"✅ Actualización masiva completada: {result['successful_updates']}/{result['total_updates']} "
            f"en {total_time:.2f}s"
        )
        
        return result

# Instancias globales
cache_manager = CacheManager()
performance_optimizer = PerformanceOptimizer(cache_manager=cache_manager)
db_optimizer = DatabaseOptimizer(cache_manager=cache_manager)

def get_cache_manager() -> CacheManager:
    """Obtiene instancia del cache manager"""
    return cache_manager

def get_performance_optimizer() -> PerformanceOptimizer:
    """Obtiene instancia del optimizador de rendimiento"""
    return performance_optimizer

def get_db_optimizer() -> DatabaseOptimizer:
    """Obtiene instancia del optimizador de DB"""
    return db_optimizer

if __name__ == "__main__":
    """Prueba del sistema de optimización"""
    print("🚀 Probando sistema de optimización...")
    
    # Probar caché
    cache = get_cache_manager()
    cache.set("test_key", {"data": "test_value"})
    cached_value = cache.get("test_key")
    print(f"✅ Cache test: {cached_value}")
    
    # Probar optimizador
    optimizer = get_performance_optimizer()
    report = optimizer.get_performance_report()
    print(f"✅ Performance report generado: {len(report)} secciones")
    
    print("📊 Revisa data/cache/ para archivos de caché")