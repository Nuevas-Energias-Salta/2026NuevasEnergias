import json

with open('extracted_movements.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

galicia = [m for m in data if m['banco'] == 'GALICIA']

print(f"Total Galicia: {len(galicia)} movimientos\n")
print("="*80)
print("ÚLTIMOS 10 MOVIMIENTOS (incluyen impuestos y comisiones):")
print("="*80)

for i, m in enumerate(galicia[-10:], start=len(galicia)-9):
    moneda = m['moneda']
    monto = m['monto']
    desc = m['descripcion'][:50]
    fecha = m['fecha']
    
    print(f"{i:2}. {fecha} | {moneda:3} {monto:12,.2f} | {desc}")

print("\n" + "="*80)
print("TODOS LOS 25 MOVIMIENTOS:")
print("="*80)

for i, m in enumerate(galicia, start=1):
    moneda = m['moneda']
    monto = m['monto']
    desc = m['descripcion'][:45]
    fecha = m['fecha']
    
    # Marcar impuestos
    es_impuesto = any(kw in desc.upper() for kw in ['COMISION', 'IVA', 'PERCEP', 'IIBB', 'DB.RG'])
    marcador = "💸" if es_impuesto else "💳"
    
    print(f"{i:2}. {marcador} {fecha} | {moneda:3} {monto:12,.2f} | {desc}")
