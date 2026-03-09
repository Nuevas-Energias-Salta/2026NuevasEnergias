import re
import json

def parse_macro_final():
    """Parser FINAL para Macro Bank OCR - extrae TODOS los consumos"""
    
    print("PARSER FINAL PARA MACRO BANK OCR")
    print("="*50)
    
    # Cargar texto OCR
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    movements = []
    
    # Mapeo completo de meses con errores OCR
    month_map = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12',
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05',
        'Jun': '06', 'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10',
        'Nov': '11', 'Dic': '12', 'Enerc': '01', 'Dicienbre': '12',
        'enerc': '01', '~gosto': '08', 'AgOSto': '08', 'Movienbre': '11',
        'enero': '01', 'diciembre': '12'
    }
    
    # Tomar la línea principal del OCR (línea 14)
    lines = text.split('\n')
    main_line = lines[13] if len(lines) > 13 else ""
    
    print(f"Analizando línea principal de {len(main_line)} caracteres...")
    
    # Dividir la línea en fragmentos usando patrones de fecha como delimitadores
    # Patrón: "día mes" + opcionalmente año
    date_pattern = r'(\d{1,2}\s+[A-Za-z]+)'
    fragments = re.split(date_pattern, main_line)
    
    print(f"Dividido en {len(fragments)} fragmentos")
    
    # Reconstruir y procesar fragmentos que comiencen con fecha
    processed = []
    current_fragment = ""
    
    for i in range(1, len(fragments), 2):
        if i + 1 < len(fragments):
            # fragments[i] es el patrón de fecha, fragments[i+1] es el contenido
            date_part = fragments[i].strip()
            content_part = fragments[i+1].strip()
            
            # Unir fecha + contenido
            full_fragment = f"{date_part} {content_part}"
            
            # Buscar el siguiente final lógico (siguiente fecha o final del texto)
            next_date_pos = len(full_fragment)
            
            # Buscar montos al final (último número con formato xx.xxx,xx)
            amount_matches = list(re.finditer(r'\d+[.,]\d{2}', full_fragment))
            if amount_matches:
                last_amount = amount_matches[-1]
                # Tomar hasta el final del monto más 20 caracteres por seguridad
                end_pos = last_amount.end()
                full_fragment = full_fragment[:end_pos]
            
            processed.append(full_fragment)
    
    print(f"Procesando {len(processed)} fragmentos con fechas...")
    
    # Analizar cada fragmento
    for idx, fragment in enumerate(processed):
        print(f"\nFragmento {idx+1}: {fragment[:80]}...")
        
        # Extraer componentes del fragmento
        # Patrón final: día mes [año] [número] descripción monto
        patterns = [
            # Día mes año número descripción monto
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{2,4})\s+(\d+)\s+([A-Za-z0-9\*\s\.\-\/]+)\s+(\d+[.,]\d{2})',
            
            # Día mes número descripción monto  
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d+)\s+([A-Za-z0-9\*\s\.\-\/]+)\s+(\d+[.,]\d{2})',
            
            # Día mes descripción monto
            r'(\d{1,2})\s+([A-Za-z]+)\s+([A-Za-z0-9\*\s\.\-\/]+)\s+(\d+[.,]\d{2})'
        ]
        
        for pattern_idx, pattern in enumerate(patterns):
            match = re.search(pattern, fragment)
            if match:
                try:
                    groups = match.groups()
                    
                    if pattern_idx == 0 and len(groups) == 6:
                        day, month, year, comp_num, desc, amount = groups
                        
                    elif pattern_idx == 1 and len(groups) == 5:
                        day, month, comp_num, desc, amount = groups
                        year = None
                        
                    elif pattern_idx == 2 and len(groups) == 4:
                        day, month, desc, amount = groups
                        comp_num = None
                        year = None
                        
                    else:
                        continue
                    
                    # Corregir mes
                    month_clean = month.strip()
                    for wrong, right in month_map.items():
                        if wrong.lower() == month_clean.lower():
                            month_clean = right
                            break
                    
                    if month_clean not in month_map.values():
                        continue
                    
                    # Formatear día
                    if len(day) == 1:
                        day = f'0{day}'
                    
                    # Determinar año
                    if year and len(year) == 2:
                        year = year
                    elif year and len(year) == 4:
                        year = year[-2:]
                    else:
                        year = '25' if month_clean == '12' else '26'
                    
                    fecha = f"{day}-{month_clean}-{year}"
                    
                    # Convertir monto
                    amount_clean = amount.replace('e8', '00').replace('e6', '00')
                    amount_clean = amount_clean.replace('e3', '00').replace('Z0,e8', '20,00')
                    amount_clean = amount_clean.replace('IC1', '').strip()
                    
                    try:
                        monto = float(amount_clean.replace('.', '').replace(',', '.'))
                    except:
                        continue
                    
                    # Corregir descripción
                    desc = desc.strip()
                    # Aplicar correcciones masivas
                    corrections = {
                        'HERPAGO': 'MERPAGO', 'MerpaGo': 'MERPAGO', 'Merpago': 'MERPAGO',
                        'ALMAYSRENTACA': 'ALWAYSRENTACA', 'ALwAYS': 'ALWAYS', 'alkays': 'ALWAYS',
                        'PANADERIACROCANTE': 'PANADERIA CROCANTE', 'JacARAKD': 'JACARANDA',
                        'SERVICAFA': 'SERVICIOS', 'SERVIF': 'SERVICIOS', 'SERVICIF-': 'SERVICIOS',
                        'CoK AR': 'COM.AR', 'CoK.AR': 'COM.AR',
                        'Sanlo': 'SAN LO', 'San Lo': 'SAN LO', 'Chico': 'CHICO',
                        'LactEA': 'LATAM', 'Faceek': 'FACEBOOK', 'Gridos': 'CHICO',
                        'ChaTGPT': 'CHATGPT', 'OPENAI': 'OPENAI',
                        'PINTURERIAS': 'PINTURERIAS', 'HRTEL': 'HARTEL',
                        'LIBRERIA': 'LIBRERIA', 'Lerma': 'LERMA',
                        'ZURICH': 'ZURICH', 'SEGURO': 'SEGURO',
                        'ACA': 'ACA', 'CAFAYATE': 'CAFAYATE',
                        'PETROGAS': 'PETROGAS', 'ESTACION': 'ESTACIÓN',
                        'JACARANDA': 'JACARANDA', 'SERVICIOS': 'SERVICIOS',
                        'LUISA': 'LUISA', 'CARRIZO': 'CARRIZO',
                        'ALWAYS': 'ALWAYS', 'RENTACA': 'RENTACA',
                        'PASAJES': 'PASAJES', 'CALZETTA': 'CALZETTA',
                        'NEUMA': 'NEUMÁTICOS'
                    }
                    
                    for wrong, right in corrections.items():
                        desc = desc.replace(wrong, right)
                    
                    # Limpiar caracteres raros
                    desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    
                    # Determinar moneda
                    is_usd = ("USD" in fragment.upper() or 
                              "dólares" in fragment.lower() or
                              "U$S" in fragment.upper() or
                              "OPENAI" in desc.upper() and monto < 100)
                    
                    moneda = "USD" if is_usd else "ARS"
                    
                    # Validar que sea consumo válido
                    if monto > 0 and len(desc) > 2:
                        # Filtrar solo pagos muy obvios (mantener la mayoría)
                        if not any(keyword in desc.upper() for keyword in ["SALDO ANTERIOR"]):
                            movement = {
                                "fecha": fecha,
                                "descripcion": desc,
                                "monto": monto,
                                "moneda": moneda,
                                "banco": "MACRO",
                                "comprobante": comp_num,
                                "original": fragment[:100] + "..." if len(fragment) > 100 else fragment
                            }
                            movements.append(movement)
                            print(f"  -> {fecha} | {moneda} {monto:10,.2f} | {desc[:40]}")
                            break
                            
                except Exception as e:
                    print(f"  ERROR: {e}")
                    continue
    
    print(f"\nTOTAL EXTRAÍDO: {len(movements)} consumos")
    
    # Guardar resultados
    if movements:
        # Separar por monedas
        ars_movements = [m for m in movements if m['moneda'] == 'ARS']
        usd_movements = [m for m in movements if m['moneda'] == 'USD']
        
        # Guardar todos los consumos
        with open("macro_consumos_completos.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        
        # Guardar separados por moneda
        with open("macro_consumos_ars.json", "w", encoding="utf-8") as f:
            json.dump(ars_movements, f, indent=4, ensure_ascii=False)
            
        with open("macro_consumos_usd.json", "w", encoding="utf-8") as f:
            json.dump(usd_movements, f, indent=4, ensure_ascii=False)
        
        print(f"\nArchivos guardados:")
        print(f"  - macro_consumos_completos.json ({len(movements)} totales)")
        print(f"  - macro_consumos_ars.json ({len(ars_movements)} en pesos)")
        print(f"  - macro_consumos_usd.json ({len(usd_movements)} en dólares)")
        
        # Top consumos
        print(f"\nTOP 10 CONSUMOS:")
        sorted_movs = sorted(movements, key=lambda x: x['monto'], reverse=True)
        for i, m in enumerate(sorted_movs[:10], 1):
            print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion'][:40]}")
    
    return movements

if __name__ == "__main__":
    movements = parse_macro_final()