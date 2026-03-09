#!/usr/bin/env python3
"""
API Wrapper mejorado con retry, logging y manejo de errores robusto
"""

import requests
import time
from typing import Dict, Any, Optional, Union
import json
from datetime import datetime
from .logger import get_logger, get_error_handler, log_function_call

class APIClient:
    """Cliente API mejorado con retry y logging automático"""
    
    def __init__(self, base_url: str, headers: Dict[str, str] = None, 
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger(f"APIClient-{base_url.split('//')[1].split('.')[0]}")
        self.error_handler = get_error_handler()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    @log_function_call()
    def make_request(self, method: str, endpoint: str, 
                    data: Optional[Dict] = None, 
                    params: Optional[Dict] = None,
                    timeout: int = 30) -> Dict[str, Any]:
        """
        Realiza llamada a API con retry automático y logging
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            
            try:
                self.logger.info(f"🌐 Llamada API: {method} {endpoint} (intento {attempt + 1})")
                
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    params=params,
                    timeout=timeout
                )
                
                response_time = time.time() - start_time
                self.logger.api_call(method, url, response.status_code, response_time)
                
                # Éxito
                if 200 <= response.status_code < 300:
                    if response.content:
                        try:
                            return {
                                "success": True,
                                "data": response.json(),
                                "status_code": response.status_code,
                                "response_time": response_time
                            }
                        except json.JSONDecodeError:
                            return {
                                "success": True,
                                "data": response.text,
                                "status_code": response.status_code,
                                "response_time": response_time
                            }
                    else:
                        return {
                            "success": True,
                            "data": None,
                            "status_code": response.status_code,
                            "response_time": response_time
                        }
                
                # Error manejable
                error_result = self.error_handler.handle_api_error(response, f"{method} {endpoint}")
                
                # Reintentar en caso de errores temporales
                if response.status_code in [429, 500, 502, 503, 504] and attempt < self.max_retries:
                    retry_delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    if response.status_code == 429:
                        retry_delay = float(response.headers.get('Retry-After', retry_delay))
                    
                    self.logger.warning(f"🔄 Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                
                return error_result
                
            except requests.exceptions.Timeout as e:
                self.error_handler.handle_exception(e, f"Timeout en {method} {endpoint}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return {"success": False, "error": "timeout", "message": str(e)}
                
            except requests.exceptions.ConnectionError as e:
                self.error_handler.handle_exception(e, f"Conexión fallida {method} {endpoint}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return {"success": False, "error": "connection_error", "message": str(e)}
                
            except Exception as e:
                return self.error_handler.handle_exception(e, f"Error inesperado {method} {endpoint}")
        
        return {"success": False, "error": "max_retries_exceeded", "message": "Máximo de reintentos alcanzado"}
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """GET request con retry"""
        return self.make_request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST request con retry"""
        return self.make_request("POST", endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PUT request con retry"""
        return self.make_request("PUT", endpoint, data=data, **kwargs)
    
    def patch(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PATCH request con retry"""
        return self.make_request("PATCH", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request con retry"""
        return self.make_request("DELETE", endpoint, **kwargs)

class NotionAPIClient(APIClient):
    """Cliente especializado para Notion API"""
    
    def __init__(self, token: str):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        super().__init__("https://api.notion.com/v1", headers, max_retries=3)
    
    def query_database(self, database_id: str, **params) -> Dict[str, Any]:
        """Consulta una base de datos de Notion"""
        return self.post(f"databases/{database_id}/query", data=params)
    
    def create_page(self, database_id: str, properties: Dict, **kwargs) -> Dict[str, Any]:
        """Crea una página en Notion"""
        data = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        data.update(kwargs)
        return self.post("pages", data=data)
    
    def update_page(self, page_id: str, properties: Dict, **kwargs) -> Dict[str, Any]:
        """Actualiza una página en Notion"""
        data = {"properties": properties}
        data.update(kwargs)
        return self.patch(f"pages/{page_id}", data=data)
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Obtiene una página de Notion"""
        return self.get(f"pages/{page_id}")

class TrelloAPIClient(APIClient):
    """Cliente especializado para Trello API"""
    
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key
        self.token = token
        self.base_params = {"key": api_key, "token": token}
        super().__init__("https://api.trello.com/1", max_retries=3)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs):
        """GET con parámetros de autenticación automáticos"""
        if params is None:
            params = {}
        params.update(self.base_params)
        return super().get(endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs):
        """POST con parámetros de autenticación automáticos"""
        if data is None:
            data = {}
        data.update(self.base_params)
        return super().post(endpoint, data=data, **kwargs)
    
    def get_boards(self) -> Dict[str, Any]:
        """Obtiene los boards del usuario"""
        return self.get("members/me/boards")
    
    def get_cards(self, board_id: str) -> Dict[str, Any]:
        """Obtiene las tarjetas de un board"""
        return self.get(f"boards/{board_id}/cards")
    
    def get_lists(self, board_id: str) -> Dict[str, Any]:
        """Obtiene las listas de un board"""
        return self.get(f"boards/{board_id}/lists")

if __name__ == "__main__":
    """Prueba de los clientes API"""
    from config.settings import config
    
    print("🧪 Probando clientes API mejorados...")
    
    # Probar Notion Client
    notion_client = NotionAPIClient(config.NOTION_TOKEN)
    print("✅ Cliente Notion creado")
    
    # Probar Trello Client  
    trello_client = TrelloAPIClient(config.TRELLO_API_KEY, config.TRELLO_TOKEN)
    print("✅ Cliente Trello creado")
    
    print("\n📝 Revisa logs/erp_*.log para ver detalles de la prueba")