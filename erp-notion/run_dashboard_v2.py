#!/usr/bin/env python3
"""
Lanzador del Dashboard V2
- Ejecuta el servidor dashboard_server_v2.py
"""

import os
import sys
import subprocess
import time

def main():
    print("=== INICIANDO DASHBOARD V2 ===")
    print("Iniciando servidor de datos...")
    
    # Ruta al script del servidor
    server_script = os.path.join(os.getcwd(), 'dashboard_server_v2.py')
    
    try:
        # Ejecutar servidor
        print(f"Ejecutando: {server_script}")
        subprocess.run(['python', server_script], check=True)
        
    except KeyboardInterrupt:
        print("\nDeteniendo sistema...")
    except Exception as e:
        print(f"Error al iniciar: {e}")
        input("Presione ENTER para salir...")

if __name__ == "__main__":
    main()
