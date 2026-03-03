import re
import json

def parse_macro_simple():
    """Parser SIMPLE para Macro - extrae todos los montos con fechas"""
    
    print("PARSER SIMPLE PARA MACRO BANK")
    print("="*40)
    
    # Cargar texto OCR
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    movements = []
    
    # Extraer línea principal
    lines = text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print(f"Procesando texto de {len(main_line)} caracteres...")
    
    # Mapeo de meses
    month_map = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12',
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05',
        'Jun': '06', 'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10',
        'Nov': '11', 'Dic': '12', 'Enerc': '01', 'Dicienbre': '12',
        'enero': '01', 'diciembre': '12', 'enerc': '01', '~gosto': '08',
        'AgOSto': '08', 'Movienbre': '11', 'Dicienbre': '12',
        'Dicieobre': '10', 'Diciendre': '12'
    }
    
    # Buscar todos los patrones: fecha + texto + monto
    # Patrón ultra simple: empieza con número, tiene texto, termina con número con coma
    pattern = r'(\d{1,2})\s+([A-Za-z]+).*?(\d+[.,]\d{2})(?=\s+\d{1,2}\s+[A-Za-z]|\s*$)'
    
    matches = list(re.finditer(pattern, main_line))
    print(f"Encontrados {len(matches)} potenciales consumos...")
    
    for i, match in enumerate(matches):
        try:
            day = match.group(1)
            month = match.group(2)
            # Tomar desde el inicio del match hasta el siguiente match o hasta encontrar el monto final
            start_pos = match.start()
            end_pos = match.end()
            
            # Texto del consumo
            consumo_text = main_line[start_pos:end_pos]
            
            # Extraer el monto (último número con coma)
            amount_match = re.search(r'(\d+[.,]\d{2})', consumo_text)
            if not amount_match:
                continue
                
            amount = amount_match.group(1)
            desc_text = consumo_text[:amount_match.start()].strip()
            
            # Corregir mes
            month_clean = month
            for wrong, right in month_map.items():
                if wrong.lower() in month_clean.lower():
                    month_clean = right
                    break
            
            if month_clean not in month_map.values():
                continue
            
            # Formatear día y año
            if len(day) == 1:
                day = f'0{day}'
            
            year = '25' if month_clean == '12' else '26'
            fecha = f"{day}-{month_clean}-{year}"
            
            # Convertir monto
            try:
                monto = float(amount.replace('.', '').replace(',', '.'))
            except:
                continue
            
            # Extraer descripción (todo entre fecha y monto)
            # Quitar el día y mes del inicio
            desc_start = f"{day} {month}"
            if consumo_text.startswith(desc_start):
                desc_text = consumo_text[len(desc_start):].strip()
            
            # Quitar el monto del final
            if desc_text.endswith(amount):
                desc_text = desc_text[:-len(amount)].strip()
            
            # Limpiar descripción
            desc = desc_text
            # Quitar números de comprobante al final
            desc = re.sub(r'\s+\d{6}\s*$', '', desc)
            desc = re.sub(r'\s+C\.\d{2}/\d{2}\s*$', '', desc)
            
            # Correcciones básicas
            desc = desc.replace('HERPAGO', 'MERPAGO')
            desc = desc.replace('MerpaGo', 'MERPAGO')
            desc = desc.replace('ALMAYSRENTACA', 'ALWAYSRENTACA')
            desc = desc.replace('ALwAYS', 'ALWAYS')
            desc = desc.replace('alkays', 'ALWAYS')
            desc = desc.replace('Sanlo', 'SAN LO')
            desc = desc.replace('Chico', 'CHICO')
            desc = desc.replace('LactEA', 'LATAM')
            desc = desc.replace('Faceek', 'FACEBOOK')
            desc = desc.replace('Gridos', 'CHICO')
            desc = desc.replace('ChaTGPT', 'CHATGPT')
            desc = desc.replace('OPENAI', 'OPENAI')
            
            # Limpiar caracteres raros
            desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            # Determinar si es USD
            is_usd = 'USD' in consumo_text.upper() or 'OPENAI' in desc
            
            # Filtrar básico
            if monto > 0 and len(desc) > 1:
                movement = {
                    "fecha": fecha,
                    "descripcion": desc,
                    "monto": monto,
                    "moneda": "USD" if is_usd else "ARS",
                    "banco": "MACRO",
                    "original": consumo_text[:100] + "..." if len(consumo_text) > 100 else consumo_text
                }
                movements.append(movement)
                print(f"{i+1:2}. {fecha} | {'USD' if is_usd else 'ARS'} {monto:10,.2f} | {desc[:40]}")
                
        except Exception as e:
            print(f"Error en match {i}: {e}")
            continue
    
    print(f"\nTOTAL EXTRAÍDO: {len(movements)} consumos")
    
    # Guardar resultados
    if movements:
        ars_movements = [m for m in movements if m['moneda'] == 'ARS']
        usd_movements = [m for m in movements if m['moneda'] == 'USD']
        
        with open("macro_consumos_simple.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        with open("macro_consumos_simple_ars.json", "w", encoding="utf-8") as f:
            json.dump(ars_movements, f, indent=4, ensure_ascii=False)
            
        with open("macro_consumos_simple_usd.json", "w", encoding="utf-8") as f:
            json.dump(usd_movements, f, indent=4, ensure_ascii=False)
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_simple.json ({len(movements)} totales)")
        print(f"  - macro_consumos_simple_ars.json ({len(ars_movements)} ARS)")
        print(f"  - macro_consumos_simple_usd.json ({len(usd_movements)} USD)")
        
        # Top consumos
        print(f"\nTOP 15 CONSUMOS:")
        sorted_movs = sorted(movements, key=lambda x: x['monto'], reverse=True)
        for i, m in enumerate(sorted_movs[:15], 1):
            print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion'][:40]}")
    
    return movements

if __name__ == "__main__":
    movements = parse_macro_simple()