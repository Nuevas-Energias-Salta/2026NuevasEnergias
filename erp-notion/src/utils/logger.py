#!/usr/bin/env python3
"""
Sistema de logging centralizado para Notion ERP
Proporciona logging estructurado y manejo de errores robusto
"""

import logging
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
import json

class ERPLogger:
    """Logger centralizado para el sistema ERP"""
    
    def __init__(self, name: str = "ERP", log_level: str = "INFO"):
        self.name = name
        self.logger = self._setup_logger(name, log_level)
        self.start_time = datetime.now()
        
    def _setup_logger(self, name: str, log_level: str) -> logging.Logger:
        """Configura el logger con handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Evitar duplicación de handlers
        if logger.handlers:
            return logger
            
        # Crear directorio de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler con timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(
            log_dir / f"erp_{timestamp}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter estructurado
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, extra: Optional[Dict] = None):
        """Log de información con metadata opcional"""
        if extra:
            self.logger.info(f"{message} | {json.dumps(extra, ensure_ascii=False)}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, extra: Optional[Dict] = None):
        """Log de advertencia"""
        if extra:
            self.logger.warning(f"{message} | {json.dumps(extra, ensure_ascii=False)}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra: Optional[Dict] = None):
        """Log de error con traceback completo"""
        error_data = {
            "error_type": type(exception).__name__ if exception else None,
            "error_message": str(exception) if exception else None,
            "traceback": traceback.format_exc() if exception else None
        }
        
        if extra:
            error_data.update(extra)
            
        self.logger.error(f"{message} | {json.dumps(error_data, ensure_ascii=False)}")
    
    def success(self, message: str, extra: Optional[Dict] = None):
        """Log de éxito (aprovecha INFO con formato especial)"""
        formatted_msg = f"✅ {message}"
        if extra:
            formatted_msg += f" | {json.dumps(extra, ensure_ascii=False)}"
        self.logger.info(formatted_msg)
    
    def script_start(self, script_name: str, parameters: Optional[Dict] = None):
        """Registra inicio de script"""
        self.info(f"🚀 Iniciando script: {script_name}", parameters)
    
    def script_end(self, script_name: str, stats: Optional[Dict] = None):
        """Registra fin de script con estadísticas"""
        duration = datetime.now() - self.start_time
        end_data = {
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration).split('.')[0]
        }
        if stats:
            end_data.update(stats)
            
        self.success(f"🏁 Finalizado script: {script_name}", end_data)
    
    def api_call(self, method: str, url: str, status: int, response_time: float = None):
        """Registra llamada a API"""
        api_data = {
            "method": method,
            "url": url,
            "status_code": status
        }
        if response_time:
            api_data["response_time_ms"] = round(response_time * 1000, 2)
            
        if 200 <= status < 300:
            self.logger.debug(f"🌐 API Call: {method} {url} - {status}")
        else:
            self.warning(f"🌐 API Call Fallida: {method} {url} - {status}", api_data)

class ErrorHandler:
    """Manejador centralizado de errores"""
    
    def __init__(self, logger: ERPLogger):
        self.logger = logger
    
    def handle_api_error(self, response, context: str = "") -> Dict:
        """Maneja errores de API de forma estructurada"""
        error_info = {
            "status_code": response.status_code,
            "url": response.url if hasattr(response, 'url') else 'unknown',
            "context": context,
            "response_text": response.text[:500] if hasattr(response, 'text') else 'no text'
        }
        
        if response.status_code == 401:
            self.logger.error("❌ Error de autenticación", extra=error_info)
            return {"success": False, "error": "auth_error", "message": "Token inválido o expirado"}
        
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '60')
            self.logger.warning(f"⏱️ Rate limit alcanzado", {**error_info, "retry_after": retry_after})
            return {"success": False, "error": "rate_limit", "retry_after": retry_after}
        
        elif response.status_code >= 500:
            self.logger.error(f"🔥 Error del servidor", extra=error_info)
            return {"success": False, "error": "server_error", "message": "Error temporal del servidor"}
        
        else:
            self.logger.error(f"❌ Error de API", extra=error_info)
            return {"success": False, "error": "api_error", "message": response.text}
    
    def handle_exception(self, exception: Exception, context: str = "") -> Dict:
        """Maneja excepciones generales"""
        error_info = {
            "context": context,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception)
        }
        
        if isinstance(exception, ConnectionError):
            self.logger.error("🔌 Error de conexión", exception, error_info)
            return {"success": False, "error": "connection_error", "message": "Error de conexión a internet"}
        
        elif isinstance(exception, TimeoutError):
            self.logger.error("⏰ Timeout", exception, error_info)
            return {"success": False, "error": "timeout", "message": "Tiempo de espera agotado"}
        
        elif isinstance(exception, FileNotFoundError):
            self.logger.error("📁 Archivo no encontrado", exception, error_info)
            return {"success": False, "error": "file_not_found", "message": "Archivo no encontrado"}
        
        else:
            self.logger.error("💥 Error inesperado", exception, error_info)
            return {"success": False, "error": "unexpected_error", "message": str(exception)}

# Instancia global del logger
global_logger = ERPLogger()
global_error_handler = ErrorHandler(global_logger)

def get_logger(name: str = None) -> ERPLogger:
    """Obtiene instancia del logger"""
    if name:
        return ERPLogger(name)
    return global_logger

def get_error_handler() -> ErrorHandler:
    """Obtiene instancia del manejador de errores"""
    return global_error_handler

# Decorador para logging automático de funciones
def log_function_call(logger_name: str = None):
    """Decorador para registrar llamadas a funciones"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = datetime.now()
            
            logger.info(f"🔄 Ejecutando función: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.success(f"✅ Función {func.__name__} completada", {"duration_seconds": duration})
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                error_handler = get_error_handler()
                error_result = error_handler.handle_exception(e, f"función {func.__name__}")
                logger.error(f"❌ Función {func.__name__} falló", e, {"duration_seconds": duration})
                raise e
                
        return wrapper
    return decorator

if __name__ == "__main__":
    """Prueba del sistema de logging"""
    logger = get_logger("TEST")
    error_handler = get_error_handler()
    
    logger.info("🧪 Iniciando prueba del sistema de logging")
    logger.success("✅ Sistema funcionando correctamente", {"test_param": "value"})
    
    try:
        # Simular un error
        raise ValueError("Este es un error de prueba")
    except Exception as e:
        error_handler.handle_exception(e, "prueba del sistema")
    
    print("\n📝 Revisa el archivo logs/erp_*.log para ver los logs completos")