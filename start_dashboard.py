#!/usr/bin/env python3
"""
Script para iniciar el dashboard del ERP
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_dashboard():
    """Iniciar el dashboard del ERP"""
    print("Iniciando Dashboard del ERP...")
    
    # Verificar que el archivo del dashboard exista
    dashboard_path = Path("data/dashboards/dashboard.html")
    if not dashboard_path.exists():
        print("No se encuentra el archivo del dashboard")
        print("Creando directorio y archivo...")
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear dashboard básico si no existe
        basic_dashboard = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notion ERP Dashboard</title>
</head>
<body>
    <h1>🚀 Notion ERP Dashboard</h1>
    <p>Cargando...</p>
</body>
</html>"""
        with open(dashboard_path, 'w') as f:
            f.write(basic_dashboard)
    
    # Iniciar el servidor API
    try:
        print("Iniciando servidor API...")
        api_script = Path("src/api/dashboard_api.py")
        
        if not api_script.exists():
            print("No se encuentra el script de la API")
            return False
        
        # Iniciar servidor en segundo plano
        process = subprocess.Popen([
            sys.executable, str(api_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar a que el servidor inicie
        time.sleep(2)
        
        # Abrir navegador
        dashboard_url = "http://localhost:8080"
        print(f"Abriendo dashboard en: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        print("Dashboard iniciado exitosamente")
        print("El dashboard está disponible en http://localhost:8080")
        print("Presiona Ctrl+C para detener el servidor")
        
        # Mantener el script corriendo
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
            process.terminate()
            process.wait()
            print("Servidor detenido")
        
        return True
        
    except Exception as e:
        print(f"Error iniciando dashboard: {e}")
        return False

if __name__ == "__main__":
    start_dashboard()