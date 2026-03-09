import re
import json

def extract_macro_despues_de_pago():
    """Extractor que encuentra 'SU PAGO EN PESOS' y extrae consumos DESPUÉS"""
    
    print("EXTRACTOR MACRO - CONSUMOS DESPUÉS DE PAGO EN PESOS")
    print("="*60)
    
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # Extraer línea principal del OCR
    lines = text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print(f"Buscando 'SU PAGO EN PESOS' en el texto...")
    
    # Encontrar dónde está "SU PAGO EN PESOS"
    pago_match = re.search(r'SU PAGO EN PESOS', main_line.upper())
    if not pago_match:
        print("No se encontró 'SU PAGO EN PESOS'")
        return []
    
    pago_pos = pago_match.end()
    print(f"Encontrado 'SU PAGO EN PESOS' en posición {pago_pos}")
    
    # Extraer todo el texto DESPUÉS de "SU PAGO EN PESOS"
    texto_despues_de_pago = main_line[pago_pos:]
    print(f"Texto después de pago (primeros 200 chars): {texto_despues_de_pago[:200]}...")
    
    movements = []
    
    # Buscar patrones de consumo en el texto después del pago
    # Patrón específico para el primer consumo después del pago:
    # "- Octubre 25 007192 PINTURERIAS HRTEL C.03/83 49262,01"
    # Patrón general para el resto de consumos
    first_pattern = r'-\s+([A-Za-záéíóúñ]+)\s+(\d{2,4})\s+(\d+)\s+([A-Za-z0-9\s\*\.\-\/]+?)\s+(\d+[.,]\d{2})'
    general_pattern = r'(\d{1,2})\s+([A-Za-záéíóúñ]+)\s+(\d+[A-Za-z0-9\s\*\.\-\/\,]*?)(\d+[.,]\d{2})'
    
    # Primero buscar el patrón del primer consumo (empieza con "- mes")
    matches = list(re.finditer(first_pattern, texto_despues_de_pago))
    
    # Si no encuentra el primer patrón, buscar el patrón general
    if len(matches) < 5:  # Si encontró pocos resultados, usar patrón general también
        general_matches = list(re.finditer(general_pattern, texto_despues_de_pago))
        matches.extend(general_matches)
    print(f"Encontrados {len(matches)} potenciales consumos después del pago...")
    
    month_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
        'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
        'nov': '11', 'dic': '12'
    }
    
    for i, match in enumerate(matches):
        try:
            # Determinar qué patrón coincidió
            if len(match.groups()) == 5:
                # Primer patrón: - mes año número descripción monto
                month = match.group(1).lower()
                year = match.group(2).strip()
                num_part = match.group(3).strip()
                desc_part = match.group(4).strip()
                amount = match.group(5)
                
                # Para el primer consumo, necesitamos encontrar el día
                # Buscar hacia atrás en el texto desde el inicio del match
                text_before = texto_despues_de_pago[:match.start()]
                day_match = re.search(r'(\d{1,2})\s*$', text_before.strip())
                if day_match:
                    day = day_match.group(1)
                else:
                    continue
                    
            elif len(match.groups()) == 4:
                # Patrón general: día mes texto monto
                day = match.group(1)
                month = match.group(2).lower()
                text_with_num = match.group(3).strip()
                amount = match.group(4)
                num_part = ""
                desc_part = text_with_num
            else:
                continue
            
            # Normalizar mes
            month_num = None
            for mes_var, codigo in month_map.items():
                if mes_var in month:
                    month_num = codigo
                    break
            
            if not month_num:
                continue
            
            # Formatear fecha
            day = f"0{day}" if len(day) == 1 else day
            year = "25" if month_num == "12" else "26"
            fecha = f"{day}-{month_num}-{year}"
            
            # Convertir monto
            try:
                monto = float(amount.replace('.', '').replace(',', '.'))
            except:
                continue
            
            # Unir número + descripción o usar descripción directa
            if num_part:
                desc = f"{num_part} {desc_part}".strip()
            else:
                desc = text_with_num.strip() if 'text_with_num' in locals() else desc_part.strip()
            
            # Separar el monto del texto para obtener la descripción limpia
            amount_in_text = re.search(r'(\d+[.,]\d{2})$', desc)
            if amount_in_text:
                desc = desc[:amount_in_text.start()].strip()
            
            # Limpiar descripción (quitar espacios extra)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            # Corregir errores comunes de OCR
            desc = desc.replace('HERPAGO', 'MERPAGO')
            desc = desc.replace('MerpaGo', 'MERPAGO')
            desc = desc.replace('ALMAYS', 'ALWAYS')
            desc = desc.replace('Sanlo', 'SAN LO')
            desc = desc.replace('Chico', 'CHICO')
            
            # Limpiar caracteres raros
            desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            # Validar que sea un consumo real (no transferencia, pago, etc.)
            desc_upper = desc.upper()
            if any(keyword in desc_upper for keyword in ["TRANSFERENCIA", "PAGO", "DEUD", "SALDO"]):
                continue
            
            # Determinar si es USD
            is_usd = 'USD' in desc.upper() or 'OPENAI' in desc.upper()
            
            if len(desc) > 2 and monto > 0:
                movement = {
                    "fecha": fecha,
                    "descripcion": desc,
                    "monto": monto,
                    "moneda": "USD" if is_usd else "ARS",
                    "banco": "MACRO",
                    "original": main_line[match.start():match.end() + 50]
                }
                movements.append(movement)
                print(f"{i+1:2}. {fecha} | {'USD' if is_usd else 'ARS'} {monto:10,.2f} | {desc[:45]}")
                
        except Exception as e:
            print(f"Error procesando consumo {i}: {e}")
            continue
    
    print(f"\nTOTAL EXTRAÍDO DESPUÉS DE PAGO: {len(movements)} consumos")
    
    # Guardar resultados
    if movements:
        with open("macro_consumos_despues_pago.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        ars_movs = [m for m in movements if m['moneda'] == 'ARS']
        usd_movs = [m for m in movements if m['moneda'] == 'USD']
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_despues_pago.json ({len(movements)} totales)")
        print(f"  - {len(ars_movs)} en ARS, {len(usd_movs)} en USD")
    
    return movements

if __name__ == "__main__":
    movements = extract_macro_despues_de_pago()