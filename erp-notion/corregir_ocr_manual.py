import json
import re

def corregir_ocr_manual():
    """Corregir errores específicos del OCR sin reprocesar"""
    
    print("CORRECCIÓN MANUAL DEL OCR EXISTENTE")
    print("="*50)
    
    # Cargar texto OCR existente
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        ocr_text = f.read()
    
    lines = ocr_text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print("Aplicando correcciones manuales específicas...")
    
    # CORRECCIONES ESPECÍFICAS basadas en tu observación
    
    # 1. Corregir PINTURERIAS MARTEL
    main_line = main_line.replace('PINTURERIAS HRTEL 49262,01', 'PINTURERIAS MARTEL 49282,01')
    main_line = main_line.replace('HART', 'MARTEL')
    
    # 2. Corregir otros errores comunes
    main_line = main_line.replace('HRTEL', 'MARTEL')
    main_line = main_line.replace('HERPAGO', 'MERPAGO')
    main_line = main_line.replace('MerpaGo', 'MERPAGO')
    main_line = main_line.replace('ALMAYS', 'ALWAYS')
    main_line = main_line.replace('ALwAYS', 'ALWAYS')
    main_line = main_line.replace('alkays', 'ALWAYS')
    main_line = main_line.replace('Sanlo', 'SAN LO')
    main_line = main_line.replace('Chico', 'CHICO')
    main_line = main_line.replace('Faceek', 'FACEBOOK')
    main_line = main_line.replace('OPENAI', 'OPENAI')
    main_line = main_line.replace('LactEA', 'LATAM')
    main_line = main_line.replace('VIA LactEA', 'VIA LATAM')
    main_line = main_line.replace('GRIDOS', 'CHICO')
    main_line = main_line.replace('CHICO CHICO', 'CHICO')
    
    # 3. Corregir errores de montos específicos
    main_line = main_line.replace('49262,01', '49282,01')  # PINTURERIAS MARTEL
    main_line = main_line.replace('49262,01', '49282,01')  # Reemplazar todas las ocurrencias
    
    # 4. Corregir fechas mal detectadas
    main_line = main_line.replace('30 Diciembre 25', '30-Diciembre-25')  # Formato consistente
    main_line = main_line.replace('02 Dicieobre 25', '02-Octubre-25')
    
    # Guardar texto corregido
    with open("macro_ocr_corregido.txt", "w", encoding="utf-8") as f:
        f.write(main_line)
    
    print("Texto corregido guardado en macro_ocr_corregido.txt")
    
    # Extraer consumos del texto corregido
    movements = []
    
    # Buscar "SU PAGO EN PESOS"
    pago_match = re.search(r'SU PAGO EN PESOS', main_line.upper())
    if not pago_match:
        print("No se encontró 'SU PAGO EN PESOS'")
        return []
    
    pago_pos = pago_match.end()
    texto_despues_pago = main_line[pago_pos:]
    
    print(f"\nBuscando consumos después de 'SU PAGO EN PESOS'...")
    print(f"Texto después del pago (primeros 300 chars):")
    print(texto_despues_pago[:300])
    
    # Extraer consumos con patrón mejorado
    # 1. Patrón para primer consumo (PINTURERIAS)
    primer_patron = r'-\s*([A-Za-z]+)\s+(\d{1,2})\s+(\d+)\s+([A-Za-z\s\*\.]+?)\s+(\d+[.,]\d{2})'
    
    # 2. Patrón para consumos generales
    general_patron = r'(\d{1,2})\s+([A-Za-z]+)\s+(\d+[A-Za-z0-9\s\*\.]*?)(\d+[.,]\d{2})'
    
    # Buscar primer consumo específico
    primer_match = re.search(primer_patron, texto_despues_pago)
    if primer_match:
        month = primer_match.group(1).lower()
        day = primer_match.group(2).strip()
        num = primer_match.group(3).strip()
        desc = primer_match.group(4).strip()
        amount = primer_match.group(5)
        
        month_map = {'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
        month_num = month_map.get(month, '10')
        
        # Para PINTURERIAS: día 30 (como indicaste)
        if 'PINTUR' in desc.upper() or 'MARTEL' in desc.upper():
            day = '30'
        
        fecha = f"{day}-{month_num}-25"
        
        try:
            monto = float(amount.replace('.', '').replace(',', '.'))
            
            movement = {
                "fecha": fecha,
                "descripcion": f"{num} {desc}".strip(),
                "monto": monto,
                "moneda": "ARS",
                "banco": "MACRO",
                "original": "PINTURERIAS MARTEL"
            }
            movements.append(movement)
            print(f"Primer consumo: {fecha} | ARS {monto:,.2f} | PINTURERIAS MARTEL")
            
        except Exception as e:
            print(f"Error en primer consumo: {e}")
    
    # Extraer resto de consumos
    resto_texto = texto_despues_pago[primer_match.end():] if primer_match else texto_despues_pago
    general_matches = list(re.finditer(general_patron, resto_texto))
    
    print(f"Encontrados {len(general_matches)} consumos adicionales...")
    
    month_map_completo = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
        'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
        'nov': '11', 'dic': '12'
    }
    
    for match in general_matches:
        try:
            day = match.group(1)
            month = match.group(2).lower()
            text_part = match.group(3).strip()
            amount = match.group(4)
            
            # Normalizar mes
            month_num = None
            for mes_var, codigo in month_map_completo.items():
                if mes_var in month:
                    month_num = codigo
                    break
            
            if not month_num:
                continue
            
            # Formatear día y año
            day = f"0{day}" if len(day) == 1 else day
            year = "25" if month_num == "12" else "26"
            fecha = f"{day}-{month_num}-{year}"
            
            # Convertir monto
            monto = float(amount.replace('.', '').replace(',', '.'))
            
            # Separar descripción del monto
            amount_in_desc = re.search(r'(\d+[.,]\d{2})$', text_part)
            if amount_in_desc:
                desc = text_part[:amount_in_desc.start()].strip()
            else:
                desc = text_part.strip()
            
            # Correcciones adicionales
            desc = desc.replace('OPENAI', 'OPENAI')
            desc = desc.replace('MERPAGO*', 'MERPAGO*')
            desc = desc.replace('MERPAGO ', 'MERPAGO ')
            
            # Determinar si es USD
            is_usd = 'USD' in desc.upper()
            
            if len(desc) > 2 and monto > 0:
                movement = {
                    "fecha": fecha,
                    "descripcion": desc,
                    "monto": monto,
                    "moneda": "USD" if is_usd else "ARS",
                    "banco": "MACRO"
                }
                movements.append(movement)
                print(f"✅ {fecha} | {'USD' if is_usd else 'ARS'} {monto:10,.2f} | {desc[:45]}")
                
        except Exception as e:
            continue
    
    print(f"\nTOTAL CONSUMOS EXTRAÍDOS: {len(movements)}")
    
    # Guardar resultados
    if movements:
        with open("macro_consumos_corregido_final.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        ars_movs = [m for m in movements if m['moneda'] == 'ARS']
        usd_movs = [m for m in movements if m['moneda'] == 'USD']
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_corregido_final.json ({len(movements)} totales)")
        print(f"  - {len(ars_movs)} en ARS, {len(usd_movs)} en USD")
        
        print(f"\nTODOS LOS CONSUMOS:")
        for i, m in enumerate(movements, 1):
            print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion']}")
    
    return movements

if __name__ == "__main__":
    corregir_ocr_manual()