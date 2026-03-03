import re
import json
from datetime import datetime

def parse_macro_streamlined():
    """Parser mejorado para OCR de Macro que maneja texto mezclado"""
    
    print("PARSER MEJORADO PARA MACRO BANK OCR")
    print("="*60)
    
    # Cargar texto OCR
    with open("macro_ocr_debug.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    movements = []
    
    # Mapeo de meses con errores de OCR
    month_map = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12',
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05',
        'Jun': '06', 'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10',
        'Nov': '11', 'Dic': '12', 'Enerc': '01', 'Dicienbre': '12',
        'enerc': '01', '~gosto': '08', 'AgOSto': '08', 'Movienbre': '11'
    }
    
    # Buscar patrones específicos en el texto grande
    # Patrón: día mes + descripción + número + monto
    patterns = [
        # Formato con número de comprobante: "26 Enero 678193 YPF Sanlo Chico 77005,00"
        r'(\d{1,2})\s+([A-Za-z]+)\s+(\d+)\s+([A-Z][A-Za-z0-9\s\*\.\-\/]+?)\s+(\d+[.,]\d{2})',
        
        # Formato sin número de comprobante: "26 Enero YPF Sanlo Chico 77005,00"
        r'(\d{1,2})\s+([A-Za-z]+)\s+([A-Z][A-Za-z0-9\s\*\.\-\/]+?)\s+(\d+[.,]\d{2})',
        
        # Formato específico para consumos USD: "87 Enero 26 698531 OPENAI *ChaTGPT inismgimcusd 20,e8 20,00"
        r'(\d{1,2})\s+([A-Za-z]+)\s+(\d+)\s+(\d+)\s+([A-Z][A-Za-z0-9\s\*\.\-\/]+?)\s+([A-Z][A-Za-z\s]+)\s+(\d+[.,]\d{2})\s+(\d+[.,]\d{2})'
    ]
    
    # Texto principal donde buscar (línea 14 del OCR)
    main_line = text.split('\n')[13] if len(text.split('\n')) > 13 else ""
    
    print(f"Buscando patrones en texto de {len(main_line)} caracteres...")
    
    found_patterns = []
    
    for pattern_idx, pattern in enumerate(patterns):
        matches = re.finditer(pattern, main_line)
        
        for match in matches:
            try:
                groups = match.groups()
                
                if pattern_idx == 0 and len(groups) == 5:
                    # Formato: día mes número descripción monto
                    day, month, comp_num, desc, amount = groups
                    
                elif pattern_idx == 1 and len(groups) == 4:
                    # Formato: día mes descripción monto
                    day, month, desc, amount = groups
                    comp_num = None
                    
                elif pattern_idx == 2 and len(groups) == 8:
                    # Formato especial USD: día mes número1 número2 descripción moneda1 monto1 monto2
                    day, month, num1, num2, desc, currency, amount1, amount2 = groups
                    comp_num = num1
                    amount = amount1 if currency.upper() == 'USD' else amount2
                    
                else:
                    continue
                
                # Corregir mes
                month_clean = month.strip()
                month_clean = month_clean.replace('Dicienbre', 'Diciembre')
                month_clean = month_clean.replace('Enerc', 'Enero')
                month_clean = month_clean.replace('~gosto', 'Agosto')
                month_clean = month_clean.replace('AgOSto', 'Agosto')
                month_clean = month_clean.replace('Movienbre', 'Noviembre')
                
                month_num = month_map.get(month_clean, '00')
                if month_num == '00':
                    print(f"  WARNING: Mes no reconocido: {month_clean}")
                    continue
                
                # Formatear día
                if len(day) == 1:
                    day = f'0{day}'
                
                # Determinar año
                year = '25' if month_num == '12' else '26'  # Dic 2025 o Ene 2026
                fecha = f"{day}-{month_num}-{year}"
                
                # Corregir monto
                amount_clean = amount.replace('e8', '00').replace('e6', '00').replace('e3', '00')
                amount_clean = amount_clean.replace('Z0,e8', '20,00')
                
                try:
                    monto = float(amount_clean.replace('.', '').replace(',', '.'))
                except:
                    continue
                
                # Corregir descripción
                desc = desc.strip()
                corrections = {
                    'HERPAGO': 'MERPAGO',
                    'MerpaGo': 'MERPAGO',
                    'MERPAGO*': 'MERPAGO*',
                    'ALMAYSRENTACA': 'ALWAYSRENTACA',
                    'ALwAYS': 'ALWAYS',
                    'alkays': 'ALWAYS',
                    'PANADERIACROCANTE': 'PANADERIA CROCANTE',
                    'JacARAKD': 'JACARANDA',
                    'SERVICAFA': 'SERVICIOS',
                    'SERVIF-': 'SERVICIOS',
                    'CoK.AR': 'COM.AR',
                    'Sanlo': 'SAN LO',
                    'Chico': 'CHICO',
                    'LactEA': 'LATAM',
                    'Faceek': 'FACEBOOK',
                    'Gridos': 'CHICO',
                    'ChaTGPT': 'CHATGPT',
                    'inismgimcusd': '',
                    'in1SjRRyC': '',
                    'SERVIF-': 'SERVICIOS'
                }
                
                for wrong, right in corrections.items():
                    desc = desc.replace(wrong, right)
                
                # Limpiar caracteres extraños
                desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()
                
                # Determinar moneda
                moneda = "USD" if "USD" in desc.upper() or "USD" in main_line[match.start():match.end() + 50].upper() else "ARS"
                
                # Validar consumo
                if monto > 0 and len(desc) > 2:
                    movement = {
                        "fecha": fecha,
                        "descripcion": desc,
                        "monto": monto,
                        "moneda": moneda,
                        "banco": "MACRO",
                        "comprobante": comp_num,
                        "original": main_line[max(0, match.start()-30):match.end()+30]
                    }
                    movements.append(movement)
                    found_patterns.append((fecha, moneda, monto, desc[:30]))
                    
            except Exception as e:
                print(f"  ERROR procesando match: {e}")
                continue
    
    print(f"\n{len(movements)} consumos encontrados:")
    for i, (fecha, moneda, monto, desc) in enumerate(found_patterns[:10], 1):
        print(f"  {i:2}. {fecha} | {moneda} {monto:10,.2f} | {desc}")
    
    if len(found_patterns) > 10:
        print(f"  ... y {len(found_patterns) - 10} más")
    
    # Guardar resultados
    if movements:
        with open("macro_consumos_finales.json", "w", encoding="utf-8") as f:
            json.dump(movements, f, indent=4, ensure_ascii=False)
        print(f"\nGuardados en macro_consumos_finales.json")
    
    return movements

if __name__ == "__main__":
    movements = parse_macro_streamlined()