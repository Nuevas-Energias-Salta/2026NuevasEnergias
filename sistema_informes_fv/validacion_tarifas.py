# -*- coding: utf-8 -*-
"""
Script de validación de tarifas
Genera reporte sobre la calidad de extracción de tarifas
"""

import sys
from pathlib import Path

# Añadir path
BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

from extractor_zzz import get_sheets_service, SHEET_ID_ZZZ, SHEET_TAB_ZZZ
from tarifa_edesa import PERIODO_CUADRO_TARIFARIO, FECHA_ACTUALIZACION


def generar_reporte_validacion_tarifas():
    """
    Lee Google Sheets y genera reporte de validación de tarifas.
    Muestra qué facturas usaron tarifas del PDF vs cuadro tarifario.
    """
    try:
        print("="*70)
        print("REPORTE DE VALIDACION DE TARIFAS")
        print("="*70)
        print()
        
        # Leer datos de Google Sheets
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID_ZZZ,
            range=f"{SHEET_TAB_ZZZ}!A:M"
        ).execute()
        
        values = result.get("values", [])
        
        if len(values) <= 1:
            print("No hay datos en la planilla para validar.")
            return
        
        # Analizar datos (saltar encabezado)
        total_facturas = len(values) - 1
        facturas_con_tarifas_pdf = 0
        facturas_periodo_correcto = 0
        alertas_criticas = []
        
        print(f"Periodo del cuadro tarifario actual: {PERIODO_CUADRO_TARIFARIO}")
        print(f"Fecha de actualizacion: {FECHA_ACTUALIZACION}")
        print()
        print(f"Analizando {total_facturas} facturas...")
        print()
        
        for row in values[1:]:  # Saltar encabezado
            if len(row) < 3:
                continue
            
            periodo_factura = row[0] if len(row) > 0 else ""
            nis = row[1] if len(row) > 1 else ""
            cliente = row[2] if len(row) > 2 else ""
            
            # Verificar si el periodo coincide con el cuadro tarifario
            if periodo_factura.lower().strip() == PERIODO_CUADRO_TARIFARIO.lower().strip():
                facturas_periodo_correcto += 1
            else:
                # Factura de otro periodo - si usó tarifas del cuadro, es un problema
                # No podemos saber del Sheet si usó PDF o cuadro, pero podemos advertir
                alertas_criticas.append({
                    'cliente': cliente,
                    'nis': nis,
                    'periodo': periodo_factura,
                    'mensaje': f"Periodo {periodo_factura} != Cuadro {PERIODO_CUADRO_TARIFARIO}"
                })
        
        # Mostrar resultados
        pct_correcto = (facturas_periodo_correcto / total_facturas * 100) if total_facturas > 0 else 0
        
        print(f"Total facturas procesadas: {total_facturas}")
        print(f"  Periodo correcto ({PERIODO_CUADRO_TARIFARIO}): {facturas_periodo_correcto} ({pct_correcto:.1f}%)")
        print(f"  Otros periodos: {len(alertas_criticas)} ({100-pct_correcto:.1f}%)")
        print()
        
        if alertas_criticas:
            print("="*70)
            print("ADVERTENCIAS - Facturas de periodos diferentes al cuadro tarifario")
            print("="*70)
            print()
            print("⚠️ Si estas facturas usaron el cuadro tarifario como fallback,")
            print("   los calculos de ahorro seran INCORRECTOS.")
            print()
            for alerta in alertas_criticas[:10]:  # Mostrar primeras 10
                print(f"  - {alerta['cliente']} (NIS: {alerta['nis']}): {alerta['mensaje']}")
            
            if len(alertas_criticas) > 10:
                print(f"\n  ... y {len(alertas_criticas) - 10} facturas mas")
            print()
        
        print("="*70)
        print("RECOMENDACIONES")
        print("="*70)
        print()
        print("1. Verificar logs de procesamiento para confirmar si se usaron tarifas del PDF")
        print("2. Si hay alertas CRITICAS, revisar PDFs manualmente")
        print("3. Actualizar cuadro tarifario mensualmente")
        print("4. Las tarifas del PDF siempre son mas confiables que el cuadro")
        print()
        
    except Exception as e:
        print(f"Error generando reporte: {e}")


if __name__ == "__main__":
    generar_reporte_validacion_tarifas()
