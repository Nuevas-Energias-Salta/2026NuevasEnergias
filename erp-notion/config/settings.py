#!/usr/bin/env python3
"""
Configuración centralizada para el sistema Notion ERP
Centraliza tokens, URLs y IDs de bases de datos para evitar duplicación
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Clase de configuración centralizada"""
    
    # API Tokens y Keys
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "YOUR_NOTION_TOKEN_HERE")
    TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "f529e10ec3bac9427b5c1abcfa2ec821")
    TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")  # Este debe ser configurado por usuario
    
    # URLs Base
    NOTION_BASE_URL = "https://api.notion.com/v1"
    TRELLO_BASE_URL = "https://api.trello.com/1"
    
    # Headers comunes
    NOTION_HEADERS = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # IDs de bases de datos Notion
    NOTION_PAGE_ID = "2dcc81c3-5804-80a3-b8a9-e5e973f5291f"
    
    # Bases de datos existentes (IDs CORRECTOS verificados)
    CENTROS_DB_ID = "2e0c81c3-5804-8159-b677-fd8b76761e2f"  # Proyectos / Obras
    CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"  # Cuentas por Cobrar (CORRECTO)
    CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"  # Cuentas por Pagar (CORRECTO)
    CLIENTES_DB_ID = "2e0c81c3-5804-8199-8d24-ded823eae751"  # Base de Clientes (contactos)
    PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"  # Base de Proveedores (contactos)
    
    # Bases de datos para el dashboard (usando las correctas)
    NOTION_PROJECTS_DB = os.getenv("NOTION_PROJECTS_DB", CENTROS_DB_ID)
    NOTION_CXC_DB = os.getenv("NOTION_CXC_DB", CXC_DB_ID)
    NOTION_CXP_DB = os.getenv("NOTION_CXP_DB", CXP_DB_ID)
    
    # Configuración de generación de cuentas
    CXC_CONFIG = {
        "generar_cuotas": True,
        "anticipo_porcentaje": 0.30,
        "numero_cuotas": 2,
        "saldo_final_porcentaje": 0.20,
        "dias_entre_cuotas": 30,
        "dias_vencimiento_anticipo": 7,
        "dias_vencimiento_cuota": 15,
        "dias_vencimiento_saldo": 30
    }
    
    CXP_CONFIG = [
        {"categoria": "Materiales", "porcentaje": 0.55},
        {"categoria": "Materiales", "porcentaje": 0.15},
        {"categoria": "Mano de Obra", "porcentaje": 0.20},
        {"categoria": "Transporte", "porcentaje": 0.05},
        {"categoria": "Otros", "porcentaje": 0.05}
    ]
    
    # Configuración de Trello
    TRELLO_BOARD_NAME = "Proyectos Soluciones Integrales"  # Ajustar según tu board
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida que la configuración es correcta"""
        errors = []
        
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN no está configurado")
            
        if not cls.TRELLO_API_KEY:
            errors.append("TRELLO_API_KEY no está configurado")
            
        if not cls.TRELLO_TOKEN:
            errors.append("TRELLO_TOKEN no está configurado")
            
        if errors:
            print("[ERROR] Errores de configuracion:")
            for error in errors:
                print(f"   - {error}")
            return False
            
        return True
    
    @classmethod
    def get_trello_params(cls) -> Dict[str, str]:
        """Retorna parámetros comunes para API de Trello"""
        return {
            'key': cls.TRELLO_API_KEY,
            'token': cls.TRELLO_TOKEN
        }
    
    @classmethod
    def get_notion_headers(cls) -> Dict[str, str]:
        """Retorna headers para API de Notion"""
        return cls.NOTION_HEADERS.copy()
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Obtener un valor de configuración"""
        return getattr(cls, key, default)

# Instancia global de configuración
config = Config()

if __name__ == "__main__":
    """Prueba de configuración"""
    print("Validando configuracion...")
    if config.validate_config():
        print("[OK] Configuracion valida")
        print(f"Notion Token: {config.NOTION_TOKEN[:10]}...")
        print(f"Trello API Key: {config.TRELLO_API_KEY[:10]}...")
    else:
        print("[ERROR] Configuracion invalida - revisa tus tokens")
