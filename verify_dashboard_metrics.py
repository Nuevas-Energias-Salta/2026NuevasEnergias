#!/usr/bin/env python3
"""
Script para verificar que los datos del Dashboard coincidan con Notion.
"""
import requests
import json

import sys
import io

# Arreglar problemas de codificación en consola Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
API_URL = "http://localhost:8086/api/dashboard"

def verify_dashboard():
    print("Iniciando verificacion de datos...")
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            metrics = data.get("metrics", {})
            
            print("\n📊 Métricas Extraídas del Servidor:")
            print("-" * 40)
            print(f"💰 INGRESOS (CxC):")
            print(f"   - Total:     ${metrics.get('income_total', 0):,.2f}")
            print(f"   - Cobrado:   ${metrics.get('income_collected', 0):,.2f}")
            print(f"   - Pendiente: ${metrics.get('income_pending', 0):,.2f}")
            
            print(f"\n💸 EGRESOS (CxP - ARS):")
            print(f"   - Total:     ${metrics.get('expenses_total', 0):,.2f}")
            print(f"   - Pagado:    ${metrics.get('expenses_paid', 0):,.2f}")
            print(f"   - Pendiente: ${metrics.get('expenses_pending', 0):,.2f}")
            
            print(f"\n💵 EGRESOS (CxP - USD):")
            print(f"   - Total USD:     U$S {metrics.get('expenses_total_usd', 0):,.2f}")
            print(f"   - Pagado USD:    U$S {metrics.get('expenses_paid_usd', 0):,.2f}")
            print(f"   - Pendiente USD: U$S {metrics.get('expenses_pending_usd', 0):,.2f}")
            
            print("-" * 40)
            print("\n✅ Instrucciones para corroborar:")
            print("1. Compara estos números con los totales de tus bases de Notion.")
            print("2. Si los números coinciden, el servidor está procesando bien los datos.")
            print("3. Abre el navegador en http://localhost:8086/data/dashboards/dashboard_standalone.html")
            print("4. Verifica que los números en pantalla sean idénticos a los de este script.")
            
        else:
            print(f"❌ Error al conectar con el servidor: {response.status_code}")
            print("Asegúrate de que 'dashboard_server_v2.py' esté corriendo.")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    verify_dashboard()
