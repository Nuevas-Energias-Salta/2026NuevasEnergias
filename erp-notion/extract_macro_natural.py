import re
import json

def extract_macro_natural():
    """Extractor NATURAL - observa patrones y extrae sin definir palabras específicas"""
    
    print("EXTRACTOR NATURAL PARA MACRO BANK")
    print("="*50)
    
    # Cargar texto OCR
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    movements = []
    
    # Extraer línea principal del OCR
    lines = text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print(f"Analizando texto natural...")
    
    # OBSERVAR: El texto tiene patrones claros de:
    # 1. Número (día)
    # 2. Palabra (mes) 
    # 3. Texto descriptivo
    # 4. Número con coma (monto)
    
    # EXTRAER todo lo que siga: [número] [palabra] ... [número,coma]
    pattern = r'(\d{1,2})\s+([A-Za-záéíóúñ]+)\s+([^0-9]*?)(\d+[.,]\d{2})(?=\s|\Z)'
    
    matches = list(re.finditer(pattern, main_line))
    print(f"Encontrados {len(matches)} patrones naturales...")
    
    month_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    for i, match in enumerate(matches):
        try:
            day = match.group(1)
            month = match.group(2).lower()
            desc = match.group(3).strip()
            amount = match.group(4)
            
            # Normalizar mes (OCR puede tener errores)
            for correct_month, code in month_map.items():
                if correct_month in month or month in correct_month:
                    month_num = code
                    break
            else:
                continue
            
            # Formatear fecha
            day = f"0{day}" if len(day) == 1 else day
            year = "25" if month_num == "12" else "26"  # Dic 2025 o resto 2026
            fecha = f"{day}-{month_num}-{year}"
            
            # Convertir monto
            try:
                monto = float(amount.replace('.', '').replace(',', '.'))
            except:
                continue
            
            # Limpiar descripción (solo espacios extras y caracteres raros)
            desc = re.sub(r'\s+', ' ', desc)
            desc = re.sub(r'[^\w\s\*\-\./]', ' ', desc)
            desc = desc.strip()
            
            # Determinar si es USD (contiene 'usd' o 'dólares' cerca)
            is_usd = 'usd' in desc.lower() or 'dólar' in desc.lower() or monto < 100 and 'openai' in desc.lower()
            
            # Extraer todo (no filtrar por palabras, solo por lógica básica)
            if monto > 0 and len(desc) > 1:
                movement = {
                    "fecha": fecha,
                    "descripcion": desc,
                    "monto": monto,
                    "moneda": "USD" if is_usd else "ARS",
                    "banco": "MACRO",
                    "original": main_line[match.start():match.end() + 50]
                }
                movements.append(movement)
                print(f"{i+1:2}. {fecha} | {'USD' if is_usd else 'ARS'} {monto:10,.2f} | {desc[:50]}")
                
        except Exception as e:
            continue
    
    print(f"\nTOTAL EXTRAÍDO: {len(movements)} consumos")
    
    # Guardar resultados
    if movements:
        with open("macro_consumos_natural.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        ars_movs = [m for m in movements if m['moneda'] == 'ARS']
        usd_movs = [m for m in movements if m['moneda'] == 'USD']
        
        with open("macro_consumos_natural_ars.json", "w", encoding="utf-8") as f:
            json.dump(ars_movs, f, indent=4, ensure_ascii=False)
            
        with open("macro_consumos_natural_usd.json", "w", encoding="utf-8") as f:
            json.dump(usd_movs, f, indent=4, ensure_ascii=False)
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_natural.json ({len(movements)} totales)")
        print(f"  - macro_consumos_natural_ars.json ({len(ars_movs)} ARS)")
        print(f"  - macro_consumos_natural_usd.json ({len(usd_movs)} USD)")
    
    return movements

if __name__ == "__main__":
    movements = extract_macro_natural()