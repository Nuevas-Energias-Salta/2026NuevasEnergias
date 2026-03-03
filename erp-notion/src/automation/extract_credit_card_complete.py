import pdfplumber
import re
import json
import os
import sys
import io
from datetime import datetime
from typing import List, Dict
import easyocr

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def detect_bank(text: str) -> str:
    """Detecta el banco basado en palabras clave en el texto del PDF"""
    text_upper = text.upper()
    if "BBVA" in text_upper or "AVBB" in text_upper or "BANCO BBVA" in text_upper:
        return "BBVA"
    if "GALICIA" in text_upper or "BANCO GALICIA" in text_upper:
        return "GALICIA"
    if "MACRO" in text_upper or "BANCO MACRO" in text_upper:
        return "MACRO"
    if "VISA BUSINESS" in text_upper:
        return "GALICIA"
    return "DESCONOCIDO"

def is_valid_consumption(description: str, amount: float) -> bool:
    """Filtra movimientos que no son consumos reales"""
    desc_upper = description.upper()
    
    # Excluir pagos y saldos únicamente
    payment_keywords = [
        'PAGO DE RESUMEN', 'SALDO ANTERIOR', 'SU PAGO EN', 
        'PAGO CUENTA', 'ABONO', 'CREDITO'
    ]
    
    # Excluir solo comisiones grandes (mantenimiento, no relacionadas a consumos)
    large_commission_keywords = [
        'COMISION MANT', 'COMISION RENO.ANUAL'
    ]
    
    # Excluir si el monto es extremadamente alto (probablemente saldo total o pago)
    if amount > 5000000:
        return False
    
    # Si es pago/saldo, excluir
    if any(keyword in desc_upper for keyword in payment_keywords):
        return False
    
    # Excluir comisiones grandes
    if any(keyword in desc_upper for keyword in large_commission_keywords):
        return False
    
    return True

def parse_galicia_enhanced(pdf) -> List[Dict]:
    """Parsea resumen de Galicia Visa Business MEJORADO"""
    movements = []
    print("   -> Procesando formato GALICIA MEJORADO...")
    
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        in_detalle_section = False
        
        for line in lines:
            if "DETALLE DEL CONSUMO" in line.upper():
                in_detalle_section = True
                continue
            
            if in_detalle_section and "TOTAL A PAGAR" in line.upper():
                in_detalle_section = False
                continue
            
            if not in_detalle_section:
                continue
            
            if "FECHA" in line and "REFERENCIA" in line and "COMPROBANTE" in line:
                continue
            
            if "Total Consumos de" in line:
                continue
            
            match = re.match(r'^(\d{2}-\d{2}-\d{2})\s+(.+)$', line)
            if not match:
                continue
            
            fecha_str = match.group(1)
            resto = match.group(2)
            parts = resto.split()
            
            if not parts:
                continue
            
            moneda = "ARS"
            if "USD" in line or "U$S" in line:
                moneda = "USD"
            
            monto_val = None
            for token in reversed(parts):
                if ',' in token and re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', token):
                    try:
                        monto_clean = token.replace('.', '').replace(',', '.')
                        monto_val = abs(float(monto_clean))
                        break
                    except:
                        continue
            
            if monto_val is None:
                continue
            
            desc = resto
            desc = re.sub(r'^[A-Z*]\s+', '', desc)
            if "USD" in desc:
                desc = desc.split("USD")[0]
            
            tokens = desc.split()
            clean_tokens = []
            for token in tokens:
                if re.match(r'^\d+$', token) and len(token) >= 5:
                    break
                if ',' in token:
                    break
                clean_tokens.append(token)
            
            desc = " ".join(clean_tokens).strip()
            
            if is_valid_consumption(desc, monto_val):
                movements.append({
                    "fecha": fecha_str,
                    "descripcion": desc,
                    "monto": monto_val,
                    "moneda": moneda,
                    "banco": "GALICIA",
                    "original": line
                })
    
    return movements

def parse_bbva_enhanced(pdf) -> List[Dict]:
    """Parsea resumen BBVA MEJORADO - DETALLE -> CONSUMOS e IMPUESTOS"""
    movements = []
    print("   -> Procesando formato BBVA MEJORADO...")
    
    months_map = {
        "Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Ago": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"
    }
    
    in_detalle_section = False
    current_section = None
    current_cardholder = None
    
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            if "DETALLE" in line.upper() and "FECHA" not in line.upper():
                in_detalle_section = True
                current_section = None
                current_cardholder = None
                continue
            
            if in_detalle_section:
                if "CONSUMO" in line.upper() and ("AGUSTIN" in line.upper() or "GABRIEL" in line.upper() or "JUAN" in line.upper()):
                    current_section = "CONSUMOS"
                    current_cardholder = line.strip()
                    continue
                
                if "IMPUESTOS" in line.upper() or ("IMPUESTO" in line.upper() and "CARGOS" in line.upper()):
                    current_section = "IMPUESTOS"
                    current_cardholder = None
                    continue
                
                if any(section in line.upper() for section in ["SALDO ACTUAL", "TOTAL GENERAL"]):
                    in_detalle_section = False
                    current_section = None
                    current_cardholder = None
                    continue
            
            if not (in_detalle_section and current_section in ["CONSUMOS", "IMPUESTOS"]):
                continue
            
            if any(header in line.upper() for header in ["FECHA DESCRIPCIÓN", "NRO. CUPÓN", "TOTAL CONSUMOS"]):
                continue
            
            match = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$', line)
            if not match:
                continue
            
            dd = match.group(1)
            mm_str = match.group(2)
            yy = match.group(3)
            resto = match.group(4)
            
            mm = months_map.get(mm_str.title(), "00")
            fecha_fmt = f"{dd}-{mm}-{yy}"
            
            tokens = resto.split()
            if len(tokens) < 2:
                continue
            
            def is_amount(s):
                return re.match(r'^-?[\d.,]+$', s) and (',' in s or '.' in s)
            
            monto_ars = None
            monto_usd = None
            
            for token in reversed(tokens):
                if is_amount(token):
                    try:
                        val = abs(float(token.replace('.', '').replace(',', '.')))
                        if monto_ars is None:
                            monto_ars = val
                        elif monto_usd is None:
                            monto_usd = val
                    except:
                        continue
            
            if monto_ars is None and monto_usd is None:
                continue
            
            desc_tokens = []
            for token in tokens:
                if is_amount(token):
                    break
                if re.match(r'^\d{6,}$', token):
                    continue
                if re.match(r'^C\.\d{2}/\d{2}$', token):
                    continue
                desc_tokens.append(token)
            
            desc = " ".join(desc_tokens).strip()
            
            if is_valid_consumption(desc, monto_ars or monto_usd or 0):
                if monto_ars and monto_ars > 0:
                    movements.append({
                        "fecha": fecha_fmt,
                        "descripcion": desc,
                        "monto": monto_ars,
                        "moneda": "ARS",
                        "banco": "BBVA",
                        "seccion": current_section,
                        "titular": current_cardholder,
                        "original": line
                    })
                
                if monto_usd and monto_usd > 0:
                    movements.append({
                        "fecha": fecha_fmt,
                        "descripcion": desc,
                        "monto": monto_usd,
                        "moneda": "USD",
                        "banco": "BBVA",
                        "seccion": current_section,
                        "titular": current_cardholder,
                        "original": line
                    })
    
    return movements

def parse_macro_with_ocr(pdf_path: str) -> List[Dict]:
    """Parsea PDF de Macro usando OCR"""
    movements = []
    print("   -> Procesando formato MACRO con OCR...")
    
    try:
        # Usar el parser simple que ya funciona
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from parse_macro_simple import parse_macro_simple
        
        # Ejecutar parser simple
        from parse_macro_simple import parse_macro_simple
        temp_movements = parse_macro_simple()
        
        # Filtrar solo consumos válidos
        for m in temp_movements:
            if is_valid_consumption(m['descripcion'], m['monto']):
                movements.append(m)
        
        print(f"   -> {len(movements)} consumos válidos de Macro")
        
    except Exception as e:
        print(f"   ❌ Error procesando Macro: {e}")
    
    return movements

def main():
    """Función principal mejorada con soporte para MACRO"""
    folder = "resumenes"
    if not os.path.exists(folder):
        print(f"Carpeta {folder} no encontrada.")
        return
    
    files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    all_movements = []
    
    print(f"🚀 SISTEMA COMPLETO DE EXTRACCIÓN DE CONSUMOS")
    print(f"Incluyendo soporte para GALICIA, BBVA y MACRO (OCR)")
    print(f"Encontrados {len(files)} archivos PDF.\n")
    
    for filename in files:
        path = os.path.join(folder, filename)
        print(f"\n{'='*80}")
        print(f"📄 Procesando: {filename}")
        print('='*80)
        
        try:
            bank = None
            
            # Detectar banco sin abrir el PDF (para Macro usar OCR directo)
            if "descarga" in filename.lower() or "macro" in filename.lower():
                bank = "MACRO"
            else:
                # Para Galicia y BBVA, leer primera página
                with pdfplumber.open(path) as pdf:
                    first_text = pdf.pages[0].extract_text() if pdf.pages else ""
                    if first_text:
                        bank = detect_bank(first_text)
            
            if not bank or bank == "DESCONOCIDO":
                print("   ⚠️  Banco no soportado o no detectado.")
                continue
            
            print(f"   🏦 Banco detectado: {bank}")
            
            movs = []
            if bank == "GALICIA":
                with pdfplumber.open(path) as pdf:
                    movs = parse_galicia_enhanced(pdf)
            elif bank == "BBVA":
                with pdfplumber.open(path) as pdf:
                    movs = parse_bbva_enhanced(pdf)
            elif bank == "MACRO":
                movs = parse_macro_with_ocr(path)
            
            print(f"   ✅ {len(movs)} consumos válidos extraídos.")
            all_movements.extend(movs)
            
        except Exception as e:
            print(f"   ❌ Error al procesar archivo: {e}")
    
    # Exportar resultados mejorados
    if all_movements:
        output_file = "extracted_movements_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_movements, f, indent=4, ensure_ascii=False)
        
        # Archivos separados por moneda y banco
        ars_movements = [m for m in all_movements if m['moneda'] == 'ARS']
        usd_movements = [m for m in all_movements if m['moneda'] == 'USD']
        
        galicia_movs = [m for m in all_movements if m['banco'] == 'GALICIA']
        bbva_movs = [m for m in all_movements if m['banco'] == 'BBVA']
        macro_movs = [m for m in all_movements if m['banco'] == 'MACRO']
        
        with open("consumos_ars_complete.json", 'w', encoding='utf-8') as f:
            json.dump(ars_movements, f, indent=4, ensure_ascii=False)
        
        with open("consumos_usd_complete.json", 'w', encoding='utf-8') as f:
            json.dump(usd_movements, f, indent=4, ensure_ascii=False)
        
        with open("consumos_galicia.json", 'w', encoding='utf-8') as f:
            json.dump(galicia_movs, f, indent=4, ensure_ascii=False)
            
        with open("consumos_bbva.json", 'w', encoding='utf-8') as f:
            json.dump(bbva_movs, f, indent=4, ensure_ascii=False)
            
        with open("consumos_macro.json", 'w', encoding='utf-8') as f:
            json.dump(macro_movs, f, indent=4, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"💾 RESULTADOS COMPLETOS GUARDADOS")
        print('='*80)
        print(f"📁 Archivo principal: {output_file} - Total: {len(all_movements)} consumos")
        print(f"💰 Consumos en ARS: consumos_ars_complete.json - {len(ars_movements)} movimientos")
        print(f"🌎 Consumos en USD: consumos_usd_complete.json - {len(usd_movements)} movimientos")
        print(f"🏦 Galicia: consumos_galicia.json - {len(galicia_movs)} movimientos")
        print(f"🏦 BBVA: consumos_bbva.json - {len(bbva_movs)} movimientos")
        print(f"🏦 Macro: consumos_macro.json - {len(macro_movements)} movimientos")
        
        print(f"\n📊 ESTADÍSTICAS:")
        banks = {}
        currencies = {}
        for m in all_movements:
            banks[m['banco']] = banks.get(m['banco'], 0) + 1
            currencies[m['moneda']] = currencies.get(m['moneda'], 0) + 1
        
        for bank, count in banks.items():
            print(f"  🏦 {bank}: {count} consumos")
        for currency, count in currencies.items():
            print(f"  💱 {currency}: {count} consumos")
        
        print(f"\n🏆 TOP 15 CONSUMOS (por monto):")
        sorted_movs = sorted(all_movements, key=lambda x: x['monto'], reverse=True)
        for i, m in enumerate(sorted_movs[:15], 1):
            print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion'][:40]}")
        
    else:
        print("\n⚠️  No se extrajeron consumos válidos.")

if __name__ == "__main__":
    main()