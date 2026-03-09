# -*- coding: utf-8 -*-
"""
Debug script para verificar qué datos se están leyendo
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "edesa_facturas" / "edesa_facturas"))

from extractor_zzz import get_sheets_service, SHEET_ID_ZZZ, SHEET_TAB_ZZZ

# Leer datos
service = get_sheets_service()
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID_ZZZ,
    range=f"{SHEET_TAB_ZZZ}!A:M"
).execute()

values = result.get("values", [])

print("="*70)
print("DEBUG: Análisis de datos de Google Sheets")
print("="*70)
print()

# Mostrar headers
if values:
    headers = values[0]
    print(f"HEADERS ENCONTRADOS ({len(headers)} columnas):")
    for i, h in enumerate(headers):
        print(f"  [{i}] {h}")
    
    print()
    print("="*70)
    print("PRIMERAS 3 FILAS DE DATOS:")
    print("="*70)
    
    for i, row in enumerate(values[1:4], 1):
        print(f"\n--- Fila {i} ---")
        for j, (header, val) in enumerate(zip(headers, row)):
            print(f"  {header}: {val}")
    
    # Convertir a diccionarios
    data = []
    for row in values[1:]:
        row_extended = row + [""] * (len(headers) - len(row))
        data.append(dict(zip(headers, row_extended)))
    
    # Buscar NIS específico
    print()
    print("="*70)
    print("BUSCANDO NIS: 3011513 (Robles)")
    print("="*70)
    
    robles_data = [d for d in data if str(d.get("NIS", "")).strip() == "3011513"]
    
    if robles_data:
        print(f"ENCONTRADOS: {len(robles_data)} registros")
        print()
        print("Primer registro:")
        for key, val in robles_data[0].items():
            print(f"  {key}: {val}")
    else:
        print("NO SE ENCONTRARON REGISTROS")
        print()
        print("Muestra de valores de NIS en la planilla:")
        nis_samples = [d.get("NIS", "") for d in data[:10]]
        for i, nis_val in enumerate(nis_samples):
            print(f"  Fila {i+1}: NIS='{nis_val}' (tipo: {type(nis_val)})")

else:
    print("ERROR: No se leyeron datos")
