import re

def debug_macro_ocr():
    """Depurar línea por línea el OCR de Macro"""
    
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    lines = text.split('\n')
    print("DEPURACIÓN LÍNEA POR LÍNEA:")
    print("="*80)
    
    # Buscar líneas que parecen consumos
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # Si contiene un día y mes al inicio
        if re.match(r'^\d{1,2}\s+[A-Za-z]', line_clean):
            print(f"\nLÍNEA {i}: {line_clean}")
            
            # Intentar extraer con regex simple
            simple_match = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(.+)', line_clean)
            if simple_match:
                day, month, rest = simple_match.groups()
                print(f"  -> Día: {day}, Mes: {month}")
                print(f"  -> Resto: {rest}")
                
                # Buscar monto al final
                amount_match = re.search(r'(\d+[.,]\d{2})$', rest)
                if amount_match:
                    amount = amount_match.group(1)
                    print(f"  -> Monto: {amount}")
                    
                    # Extraer descripción (todo antes del monto)
                    desc = rest[:amount_match.start()].strip()
                    print(f"  -> Descripción: {desc}")

if __name__ == "__main__":
    debug_macro_ocr()