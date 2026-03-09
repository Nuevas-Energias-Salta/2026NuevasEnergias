import re
import json

def extract_macro_observador():
    """EXTRACTOR OBSERVADOR - ve lo que hay y extrae sin predefinir"""
    
    print("EXTRACTOR OBSERVADOR PARA MACRO BANK")
    print("="*50)
    
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # Extraer la línea principal del OCR
    lines = text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print(f"Observando texto de {len(main_line)} caracteres...")
    print("Buscando patrones naturales sin predefinir...")
    
    movements = []
    
    # OBSERVAR Y EXTRAER: Buscar secuencias de números con comas
    # Si hay un número con coma, buscar hacia atrás la fecha y descripción
    
    # Encontrar todos los montos posibles (números con dos decimales)
    amount_positions = []
    for match in re.finditer(r'(\d{1,3}(?:\.\d{3})*,\d{2})', main_line):
        amount_positions.append((match.start(), match.end(), match.group(1)))
    
    print(f"Encontrados {len(amount_positions)} montos posibles...")
    
    # Para cada monto, buscar hacia atrás para encontrar fecha y descripción
    for i, (start, end, amount_str) in enumerate(amount_positions):
        try:
            # Texto antes del monto
            before_amount = main_line[:start]
            
            # Buscar la fecha más cercana hacia atrás
            # Patrón: número (día) + letras (mes)
            date_match = None
            for match in reversed(list(re.finditer(r'(\d{1,2})\s+([A-Za-z]+)', before_amount))):
                date_match = match
                break
            
            if not date_match:
                continue
            
            day = date_match.group(1)
            month_raw = date_match.group(2)
            
            # Texto entre fecha y monto = descripción + posibles números
            desc_text = before_amount[date_match.end():].strip()
            
            # Convertir monto
            try:
                amount = float(amount_str.replace('.', '').replace(',', '.'))
            except:
                continue
            
            # Si el monto es muy chico, ignorar (pero permitir hasta 2 millones)
            if amount < 1 or amount > 2000000:
                continue
            
            # Normalizar mes (intentar con diferentes variaciones)
            month_variations = {
                'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
                'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
                'nov': '11', 'dic': '12'
            }
            
            month_lower = month_raw.lower()
            month_num = None
            
            for variation, code in month_variations.items():
                if variation in month_lower:
                    month_num = code
                    break
            
            if not month_num:
                continue
            
            # Formatear fecha
            day = f"0{day}" if len(day) == 1 else day
            year = "25" if month_num == "12" else "26"
            fecha = f"{day}-{month_num}-{year}"
            
            # LIMPIAR descripción - quitar números al final
            # Separar por espacios y quitar últimos tokens que parecen números
            desc_parts = desc_text.split()
            clean_parts = []
            
            for part in desc_parts:
                # Si encontramos un número, dejamos de agregar a la descripción
                if re.match(r'^\d+$', part) or re.match(r'^\d+[.,]\d{2}$', part):
                    break
                # Si parece un número de comprobante
                if re.match(r'^\d{6}$', part):
                    break
                # Si es cuota
                if re.match(r'^C\.\d{2}/\d{2}$', part):
                    break
                clean_parts.append(part)
            
            desc = " ".join(clean_parts).strip()
            
            # Si después de limpiar queda algo vacío, intentar otra aproximación
            if len(desc) < 3:
                # Quitar solo números exactos al final
                if desc_parts:
                    desc_parts.pop()  # Quitar último
                    desc = " ".join(desc_parts).strip()
            
            # Corregir errores obvios de OCR
            desc = desc.replace('HERPAGO', 'MERPAGO')
            desc = desc.replace('MerpaGo', 'MERPAGO')
            desc = desc.replace('ALMAYS', 'ALWAYS')
            desc = desc.replace('Sanlo', 'SAN LO')
            desc = desc.replace('Chico', 'CHICO')
            desc = desc.replace('Faceek', 'FACEBOOK')
            desc = desc.replace('OPENAI', 'OPENAI')
            
            # Limpiar caracteres raros pero mantener espacios
            desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            # Determinar si es USD
            text_around = main_line[max(0, start-30):end+30]
            is_usd = 'usd' in text_around.lower() or 'openai' in desc.lower()
            
            # VALIDACIÓN ESPECÍFICA: 
            # 1. Si es "su pago en pesos", IGNORAR este consumo
            # 2. Extraer solo consumos que vienen DESPUÉS de "su pago en pesos"
            desc_upper = desc.upper()
            
            # Si es "SU PAGO EN PESOS", marcar que empezaron los consumos
            if "SU PAGO EN PESOS" in desc_upper:
                # No guardar este movimiento, pero marcar para que los siguientes sí se extraigan
                continue
            
            # Si es transferencia o relacionados con pagos, no extraer
            if any(keyword in desc_upper for keyword in ["TRANSFERENCIA", "DEUD -", "PAGO"]):
                continue
                
                movement = {
                    "fecha": fecha,
                    "descripcion": desc,
                    "monto": amount,
                    "moneda": "USD" if is_usd else "ARS",
                    "banco": "MACRO",
                    "original": text_around[:80] + "..." if len(text_around) > 80 else text_around
                }
                movements.append(movement)
                print(f"{len(movements):2}. {fecha} | {'USD' if is_usd else 'ARS'} {amount:10,.2f} | {desc[:45]}")
                
        except Exception as e:
            print(f"Error procesando monto {i}: {e}")
            continue
    
    print(f"\nTOTAL OBSERVADO Y EXTRAÍDO: {len(movements)} consumos")
    
    # Guardar resultados
    if movements:
        with open("macro_consumos_observador.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        ars_movs = [m for m in movements if m['moneda'] == 'ARS']
        usd_movs = [m for m in movements if m['moneda'] == 'USD']
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_observador.json ({len(movements)} totales)")
        print(f"  - {len(ars_movs)} en ARS, {len(usd_movs)} en USD")
        
        # Mostrar todos los consumos encontrados
        print(f"\nTODOS LOS CONSUMOS ENCONTRADOS:")
        for i, m in enumerate(movements, 1):
            print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion']}")
    
    return movements

if __name__ == "__main__":
    movements = extract_macro_observador()