"""Test del parser Galicia con el texto exacto del usuario."""
import sys, io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from cargador_universal_gui import ExtractionEngine

texto = """12-05-25 K MERPAGO*OVERHARD 09/18 486050 110.888,83 
05-08-25 * MERPAGO*CORRAL 06/12 724845 162.826,33 
18-09-25 * NEUMATICOS SAN AGUST 05/12 000572 22.416,66 
25-09-25 * NEUMATICOS SAN AGUST 04/12 000170 28.666,66 
28-12-25 K OPENAI *CHATGPT  in1SjRRyCUSD       20,00 188369 20,00
28-12-25 F LinkedIn SN P696 LinkedIn USD        6,40 302622 6,40
30-12-25 * APPYPF 02537 COMBUST 537614 90.005,94 
06-01-26 E NOCRM.IO                  USD      160,00 494224 160,00
10-01-26 GOOGLE *Google O P1hGQsii USD       19,99 457354 19,99
10-01-26 GOOGLE *Instagra P1hIXnfU USD       11,99 505985 11,99
12-01-26 * VISTAGE SA       000C30715743112 185492 898.788,00 
13-01-26 F SLACK T08S0A7LAFR         USD       50,58 167128 50,58
13-01-26 K TRELLO.COM* ATLA          USD       42,00 496481 42,00
15-01-26 * GALICIA SEGURO0456398000001-005-032 998801 42.391,76"""

engine = ExtractionEngine()
items = engine.extraer_galicia_texto(texto)

print(f"Total items: {len(items)}")
print(f"{'#':>2} {'Fecha':10} {'Moneda':5} {'Monto':>12} {'Cupon':7} {'Cuotas':6} Descripcion")
print("-" * 90)

for i, it in enumerate(items, 1):
    print(f"{i:2} {it['fecha']:10} {it['moneda']:5} {it['monto']:>12,.2f} {it['cupon']:7} {it['cuotas']:6} {it['descripcion'][:40]}")

# Verificar: debe haber exactamente 14 items (1 por linea)
print(f"\n--- Resumen ---")
n_ars = sum(1 for it in items if it['moneda'] == 'ARS')
n_usd = sum(1 for it in items if it['moneda'] == 'USD')
total_ars = sum(it['monto'] for it in items if it['moneda'] == 'ARS')
total_usd = sum(it['monto'] for it in items if it['moneda'] == 'USD')
print(f"ARS: {n_ars} items, total {total_ars:,.2f}")
print(f"USD: {n_usd} items, total {total_usd:,.2f}")
print(f"Bancos: {set(it['banco'] for it in items)}")

# Validaciones
assert len(items) == 14, f"Deberian ser 14 items, hay {len(items)}"
assert n_usd == 7, f"Deberian ser 7 USD, hay {n_usd}"
assert n_ars == 7, f"Deberian ser 7 ARS, hay {n_ars}"
assert 'GALICIA' in set(it['banco'] for it in items), "Todos deben ser banco GALICIA"
print("\nTODO OK!")
