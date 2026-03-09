import json
from collections import Counter
from datetime import datetime

# Cargar datos extraídos
with open('extracted_movements.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total movimientos extraídos: {len(data)}")
print("\n" + "="*60)

# Analizar por banco
bancos = Counter([m['banco'] for m in data])
print("\nDistribución por banco:")
for banco, count in bancos.items():
    print(f"  {banco}: {count} movimientos")

# Analizar fechas de Galicia
galicia = [m for m in data if m['banco'] == 'GALICIA']
print(f"\n{'='*60}")
print(f"GALICIA - Total: {len(galicia)} movimientos")
print("="*60)

# Ver distribución de meses
fechas_galicia = [m['fecha'] for m in galicia]
meses = Counter([f.split('-')[1] for f in fechas_galicia])
print("\nDistribución por mes (Galicia):")
for mes, count in sorted(meses.items()):
    mes_nombre = {
        '01': 'Enero', '05': 'Mayo', '08': 'Agosto', 
        '09': 'Septiembre', '12': 'Diciembre'
    }.get(mes, f'Mes {mes}')
    print(f"  {mes_nombre} (mes {mes}): {count} movimientos")

# Ver consumos en cuotas vs consumos nuevos
print("\n" + "="*60)
print("ANÁLISIS DE CUOTAS (primeros 20):")
print("="*60)

for i, m in enumerate(galicia[:20], 1):
    original = m['original']
    fecha = m['fecha']
    
    # Detectar cuotas
    cuota_info = ""
    if '/' in original:
        # Buscar patrón XX/YY
        import re
        cuota_match = re.search(r'(\d{2})/(\d{2})', original)
        if cuota_match:
            cuota_actual = cuota_match.group(1)
            cuota_total = cuota_match.group(2)
            cuota_info = f" [CUOTA {cuota_actual}/{cuota_total}]"
    
    print(f"{i:2}. {fecha} {cuota_info:20} | {original[:70]}")

# Resumen del problema
print("\n" + "="*60)
print("PROBLEMA DETECTADO:")
print("="*60)
print("""
El resumen es de ENERO 2026 (fecha 22-01-26 visible en encabezado)
Pero incluye consumos de:
  - Mayo 2025 (12-05-25) - CUOTA 9/18 de una compra antigua
  - Agosto 2025 (05-08-25) - CUOTA 6/12 de una compra antigua
  - Septiembre 2025 - CUOTAS 4/12 y 5/12
  - Diciembre 2025 - Consumos normales del mes anterior
  - Enero 2026 - Consumos del período actual

SOLUCIÓN NECESARIA:
Solo extraer consumos del MES DEL RESUMEN (Enero 2026)
O identificar el período de facturación del resumen.
""")
