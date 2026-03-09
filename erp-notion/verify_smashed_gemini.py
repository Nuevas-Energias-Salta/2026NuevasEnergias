from cargador_universal_gui import ExtractionEngine

def test_smashed_gemini():
    engine = ExtractionEngine()
    smashed_text = """
FechaComercioNro. CupónCuotaImporte ($)Importe (US$)03-Sep-24ENERGE S.A. 000070 11/12 274.506,00 11-Sep-24ENERGE S.A. 000078 11/12 210.783,04 19-May-25MERPAGO ALWAYSRENTACA 231812 03/03 84.605,93 07-Jul-25MERPAGO POWERMETER 612239 -90.000,00 07-Jul-25SANCOR COOP SE0000099044732 009615 -6.176,00 08-Jul-25NOCRM.IO USD 128,00 539001 -151.096,22 128,00 17-Jul-25MERPAGO ALWAYSRENTACA 537616 -113.031,20 17-Jul-25ZURICH SEGUROS 005801 -0,00 25-Jul-25CABLE EXPRESS 000001 -66.117,80 Total996.316,19 128,00 
"""
    # Simulate the user's paste (multiple transactions in one line or split by newline)
    # The user's input came in as one long string with dates embedded.
    # Our current logic handles line-by-line. If the user pasted it as one line, 
    # we might need to pre-split it by date patterns.
    
    # Pre-processing: If it's a single giant line, split by date pattern
    text_to_parse = smashed_text
    import re
    if len(text_to_parse.split('\n')) < 3: # Likely smashed into few lines
        # Split by DD-Mon-YY
        text_to_parse = re.sub(r'(\d{2}-[A-Za-z]{3}-\d{2})', r'\n\1', text_to_parse)

    items = engine.extraer_gemini_markdown(text_to_parse)
    print(f"Extracted {len(items)} items:")
    for it in items:
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['fecha']} | {it['descripcion']} ({it['cupon']})")

if __name__ == "__main__":
    test_smashed_gemini()
