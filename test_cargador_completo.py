"""Test rapido: verifica que el cargador parsea correctamente el texto de Macro."""
import re, sys, io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from cargador_universal_gui import ExtractionEngine

engine = ExtractionEngine()
engine.col_offsets = {"PESOS": -1, "DOLARES": -1}

with open('pegar_resumen_aqui.txt', 'r', encoding='utf-8') as f:
    texto = f.read()

# Simular procesar_texto con banco=MACRO
banco = "MACRO"

# Detectar formato
tiene_tabs = '\t' in texto
es_gemini_md = '|' in texto and ('Fecha' in texto or 'Importe' in texto)
es_gemini_smashed = bool(re.search(r'\d{2}-[A-Za-z]{3}-\d{2}', texto)) and not bool(re.search(r'\d{1,2}\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\s+\d{2}', texto, re.IGNORECASE))
tiene_macro = bool(re.search(r'\d{1,2}\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\s+\d{2}', texto, re.IGNORECASE))

if tiene_tabs:
    parser = "TABS"
elif es_gemini_md:
    parser = "GEMINI_MD"  
elif es_gemini_smashed:
    parser = "GEMINI_SMASHED"
else:
    parser = banco

print(f"Parser: {parser}")
assert parser == "MACRO", f"ERROR: Deberia ser MACRO, fue {parser}"

items = engine.extraer_macro_texto(texto)
print(f"Items: {len(items)}")

# Verificar bancos 
bancos_en_items = set(it.get('banco', '?') for it in items)
print(f"Bancos en items: {bancos_en_items}")
assert 'GEMINI' not in bancos_en_items, "ERROR: Hay items con banco GEMINI!"

# Verificar fechas
from datetime import datetime
errores = 0
for it in items:
    try:
        parts = it['fecha'].split('-')
        d, m, y = parts[0], parts[1], parts[2]
        if len(y) == 2: y = f"20{y}"
        datetime.strptime(f"{y}-{m}-{d}", "%Y-%m-%d")
    except:
        print(f"  Fecha invalida: {it['fecha']} -> {it['descripcion']}")
        errores += 1

total_ars = sum(it['monto'] for it in items if it['moneda'] == 'ARS')
total_usd = sum(it['monto'] for it in items if it['moneda'] == 'USD')
print(f"Total ARS: {total_ars:,.2f}")
print(f"Total USD: {total_usd:,.2f}")
print(f"Fechas invalidas: {errores}")
print(f"\nRESULTADO: {'OK' if errores == 0 else 'ERRORES'}")
