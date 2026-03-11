# -*- coding: utf-8 -*-
"""
Script para forzar la generación de los informes del mes de ENERO 2026,
ignorando los registros posteriores de Febrero y Marzo en el Google Sheets.
"""

import sys
from pathlib import Path
import datetime

BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

from generar_informes import (
    leer_datos_sheets, 
    calcular_metricas_nis, 
    generar_html_informe,
    NIS_NOMBRES
)

def procesar_informes_enero():
    print("📥 Leyendo todos los datos del Google Sheets...")
    datos = leer_datos_sheets()
    
    if not datos:
        print("⚠️ No se pudieron leer los datos.")
        return
        
    # Filtrar registros que sean de Febrero 2026 o Marzo 2026
    # Para obligar al script a tratar Enero como el "último mes"
    datos_enero = []
    ignorados = 0
    for d in datos:
        fecha_str = str(d.get("   Fecha ", "")).strip().lower()
        if not fecha_str:
            datos_enero.append(d)
            continue
            
        if ("feb" in fecha_str or "mar" in fecha_str) and "2026" in fecha_str:
            ignorados += 1
            continue
            
        datos_enero.append(d)

    print(f"✅ Se ignoraron {ignorados} registros más recientes (Feb/Mar) para simular Enero.")
    
    output_dir = BASE_DIR / "Informes_01_2026"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    informes_generados = 0
    total_clientes = len(NIS_NOMBRES)
    
    print(f"📊 Generando informes de Enero para {total_clientes} clientes...")
    
    for idx, (nis, nombre) in enumerate(NIS_NOMBRES.items(), 1):
        print(f"  [{idx}/{total_clientes}] Procesando NIS {nis}: {nombre}...")
        
        # Le pasamos nuestra lista filtrada 'datos_enero'
        metricas = calcular_metricas_nis(datos_enero, nis)
        
        if not metricas:
            print(f"    ⚠️ No hay suficientes datos para {nombre}")
            continue
            
        html = generar_html_informe(metricas).strip()
        filename = f"informe_{nis}_{nombre.replace(' ', '_')}.html"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
            
        informes_generados += 1
        
    print("-" * 50)
    print(f"🎉 COMPLETADO: Se generaron {informes_generados} informes locales de ENERO en '\\Informes_01_2026'")
    print("-" * 50)

if __name__ == "__main__":
    procesar_informes_enero()
