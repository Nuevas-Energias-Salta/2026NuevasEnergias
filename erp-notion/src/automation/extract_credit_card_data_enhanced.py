import pdfplumber
import re
import json
import os
import sys
import io
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def detect_bank(text: str) -> str:
    """Detecta el banco basado en palabras clave en el texto del PDF"""
    text_upper = text.upper()
    if "BBVA" in text_upper or "AVBB" in text_upper or "BANCO BBVA" in text_upper:
        return "BBVA"
    if "GALICIA" in text_upper or "BANCO GALICIA" in text_upper:
        return "GALICIA"
    if "VISA BUSINESS" in text_upper:
        return "GALICIA"
    return "DESCONOCIDO"

def extract_billing_period(text: str) -> Optional[Tuple[str, str]]:
    """
    Extrae el período de facturación del resumen
    Retorna tuple (fecha_inicio, fecha_fin) o None si no se encuentra
    """
    # Patrones comunes para períodos de facturación
    patterns = [
        r'Periodo\s+(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})',
        r'Período\s+(\d{2}/\d{2}/\d{4})\s+al\s+(\d{2}/\d{2}/\d{4})',
        r'Resumen.*?(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})',
        r'Facturación.*?(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})',
        r'Del\s+(\d{2}/\d{2}/\d{4})\s+al\s+(\d{2}/\d{2}/\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    
    return None

def is_date_in_period(date_str: str, period_start: str, period_end: str) -> bool:
    """
    Verifica si una fecha está dentro del período de facturación
    date_str: formato DD-MM-YY o DD-MMM-YY
    period_start/period_end: formato DD/MM/YYYY
    """
    try:
        # Convertir fecha del movimiento a datetime
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                if month.isalpha():
                    # Mes en texto (Ene, Feb, etc.)
                    months = {'Ene': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
                             'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                             'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
                    month = months.get(month.title(), month)
                
                movement_date = datetime.strptime(f'{day}-{month}-{year}', '%d-%m-%Y')
            else:
                return False
        
        # Convertir fechas del período a datetime
        start_date = datetime.strptime(period_start, '%d/%m/%Y')
        end_date = datetime.strptime(period_end, '%d/%m/%Y')
        
        return start_date <= movement_date <= end_date
        
    except Exception:
        return False

def is_valid_consumption(description: str, amount: float) -> bool:
    """
    Filtra movimientos que no son consumos reales
    MANTIENE cuotas de meses anteriores (compras financiadas)
    """
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
    if amount > 5000000:  # Más de 5 millones probablemente no es un consumo
        return False
    
    # Si es pago/saldo, excluir
    if any(keyword in desc_upper for keyword in payment_keywords):
        return False
    
    # Excluir comisiones grandes
    if any(keyword in desc_upper for keyword in large_commission_keywords):
        return False
    
    # Incluir todo lo demás:
    # - Cuotas de compras anteriores (ej: "MERPAGO*ALWAYSRENTACA C.01/06")
    # - Consumos nuevos del período
    # - Impuestos y percepciones (están relacionados a los consumos)
    # - Seguros cargados a la tarjeta
    
    return True

def parse_galicia_enhanced(pdf) -> List[Dict]:
    """
    Parsea resumen de Galicia Visa Business MEJORADO
    SOLO extrae consumos del período de facturación actual
    Filtra correctamente consumos vs pagos/comisiones
    """
    movements = []
    
    print("   -> Procesando formato GALICIA MEJORADO...")
    
    # Extraer período de facturación
    full_text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"
    
    billing_period = extract_billing_period(full_text)
    if billing_period:
        period_start, period_end = billing_period
        print(f"   -> ✓ Período detectado: {period_start} → {period_end}")
    else:
        print("   -> ⚠️  No se pudo detectar el período de facturación")
        period_start, period_end = None, None
    
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        in_detalle_section = False
        
        for line_num, line in enumerate(lines):
            # Detectar inicio de sección DETALLE DEL CONSUMO
            if "DETALLE DEL CONSUMO" in line.upper():
                in_detalle_section = True
                print(f"   -> ✓ Sección DETALLE DEL CONSUMO encontrada (página {page_num + 1})")
                continue
            
            # Detectar fin de sección
            if in_detalle_section and ("TOTAL A PAGAR" in line.upper() or 
                                      "RESUMEN DEL PERIODO" in line.upper()):
                in_detalle_section = False
                print(f"   -> ✓ Fin de sección DETALLE DEL CONSUMO")
                continue
            
            # Solo procesar líneas dentro de la sección
            if not in_detalle_section:
                continue
            
            # Ignorar encabezados
            if any(header in line.upper() for header in ["FECHA", "REFERENCIA", "COMPROBANTE"]):
                continue
            
            # Ignorar subtotales por tarjeta
            if "Total Consumos de" in line:
                continue
            
            # Buscar líneas con formato de fecha DD-MM-YY al inicio
            match = re.match(r'^(\d{2}-\d{2}-\d{2})\s+(.+)$', line)
            if not match:
                continue
            
            fecha_str = match.group(1)
            resto = match.group(2)
            parts = resto.split()
            
            if not parts:
                continue
            
            # Determinar moneda
            moneda = "ARS"
            if "USD" in line or "U$S" in line:
                moneda = "USD"
            
            # Extraer monto (último token con formato numérico argentino)
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
            
            # Extraer descripción (limpieza mejorada)
            desc = resto
            # Quitar letra inicial (K, F, E, * etc)
            desc = re.sub(r'^[A-Z*]\s+', '', desc)
            # Quitar USD si está
            if "USD" in desc:
                desc = desc.split("USD")[0]
            # Quitar cupones y números de comprobante
            desc = re.sub(r'\s+\d{6,}\s*$', '', desc)  # Números de comprobante al final
            desc = re.sub(r'\s+\d{2}\/\d{2}\s*$', '', desc)  # Cuotas al final
            
            # Quitar tokens numéricos del final
            tokens = desc.split()
            clean_tokens = []
            for token in tokens:
                # Detener si encontramos números que parecen montos o comprobantes
                if re.match(r'^\d+$', token) and len(token) >= 5:  # Comprobante
                    break
                if ',' in token:  # Monto
                    break
                clean_tokens.append(token)
            
            desc = " ".join(clean_tokens).strip()
            
            # Filtrar por período si está disponible
            if period_start and period_end:
                if not is_date_in_period(fecha_str, period_start, period_end):
                    print(f"      ⏭️  Fuera de período: {fecha_str} - {desc[:50]}...")
                    continue
            
            # Validar que sea un consumo real
            if not is_valid_consumption(desc, monto_val):
                print(f"      🚫 No es consumo: {fecha_str} - {desc[:50]}... (${monto_val:,.2f})")
                continue
            
            # Guardar movimiento
            movement = {
                "fecha": fecha_str,
                "descripcion": desc,
                "monto": monto_val,
                "moneda": moneda,
                "banco": "GALICIA",
                "original": line
            }
            movements.append(movement)
            print(f"      ✅ Consumo válido: {fecha_str} | {moneda} {monto_val:,.2f} | {desc[:50]}...")
    
    return movements

def parse_bbva_enhanced(pdf) -> List[Dict]:
    """
    Parsea resumen BBVA MEJORADO
    SOLO extrae de la sección DETALLE -> CONSUMOS (todos los titulares) y DETALLE -> IMPUESTOS
    """
    movements = []
    print("   -> Procesando formato BBVA MEJORADO...")
    print("   -> Buscando sección DETALLE...")
    
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
            # Detectar sección DETALLE principal
            if "DETALLE" in line.upper() and "FECHA" not in line.upper():
                in_detalle_section = True
                current_section = None
                current_cardholder = None
                print(f"   -> ✓ Sección DETALLE encontrada (página {page_num + 1})")
                continue
            
            # Detectar subsecciones dentro de DETALLE
            if in_detalle_section:
                # Consumos por titular (ej: "Consumos Agustin Isasmendi")
                if "CONSUMOS" in line.upper() and ("AGUSTIN" in line.upper() or "GABRIEL" in line.upper() or "JUAN" in line.upper()):
                    current_section = "CONSUMOS"
                    current_cardholder = line.strip()
                    print(f"      ✓ Sección: {current_cardholder}")
                    continue
                
                # Sección de impuestos
                if "IMPUESTOS" in line.upper() or ("IMPUESTO" in line.upper() and "CARGOS" in line.upper()):
                    current_section = "IMPUESTOS"
                    current_cardholder = None
                    print(f"      ✓ Sección: IMPUESTOS, CARGOS E INTERESES")
                    continue
                
                # Fin de sección DETALLE (cuando aparece otra sección principal)
                if any(section in line.upper() for section in ["SALDO ACTUAL", "TOTAL GENERAL"]):
                    in_detalle_section = False
                    current_section = None
                    current_cardholder = None
                    print(f"      ✓ Fin de sección DETALLE")
                    continue
            
            # Solo procesar si estamos en DETALLE con sección CONSUMOS o IMPUESTOS
            if not (in_detalle_section and current_section in ["CONSUMOS", "IMPUESTOS"]):
                continue
            
            # Ignorar líneas de encabezado
            if any(header in line.upper() for header in ["FECHA DESCRIPCIÓN", "NRO. CUPÓN", "TOTAL CONSUMOS"]):
                continue
            
            # Patrón BBVA: DD-MMM-YY (ej: 06-Ago-25)
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
            
            # Función para verificar si es monto
            def is_amount(s):
                return re.match(r'^-?[\d.,]+$', s) and (',' in s or '.' in s)
            
            # Extraer montos de la línea (puede haber pesos y dólares)
            monto_ars = None
            monto_usd = None
            
            # Buscar montos al final de la línea
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
            
            # Si no hay montos válidos, continuar
            if monto_ars is None and monto_usd is None:
                continue
            
            # Extraer descripción (quitando montos y números de cupón)
            desc_tokens = []
            for token in tokens:
                # Detener en montos
                if is_amount(token):
                    break
                # Ignorar números de cupón
                if re.match(r'^\d{6,}$', token):
                    continue
                # Ignorar cuotas
                if re.match(r'^C\.\d{2}/\d{2}$', token):
                    continue
                desc_tokens.append(token)
            
            desc = " ".join(desc_tokens).strip()
            
            # Validar que sea un consumo real
            if not is_valid_consumption(desc, monto_ars or monto_usd or 0):
                print(f"      🚫 No es consumo: {fecha_fmt} - {desc[:50]}...")
                continue
            
            # Agregar movimientos según moneda
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
                print(f"      ✅ {current_section}: {fecha_fmt} | ARS {monto_ars:,.2f} | {desc[:50]}...")
            
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
                print(f"      ✅ {current_section}: {fecha_fmt} | USD {monto_usd:,.2f} | {desc[:50]}...")
    
    return movements

def main():
    """Función principal mejorada"""
    folder = "resumenes"
    if not os.path.exists(folder):
        print(f"Carpeta {folder} no encontrada.")
        return
    
    files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    all_movements = []
    
    print(f"🚀 SISTEMA MEJORADO DE EXTRACCIÓN DE CONSUMOS")
    print(f"Encontrados {len(files)} archivos PDF.\n")
    
    for filename in files:
        path = os.path.join(folder, filename)
        print(f"\n{'='*80}")
        print(f"📄 Procesando: {filename}")
        print('='*80)
        
        try:
            with pdfplumber.open(path) as pdf:
                first_text = pdf.pages[0].extract_text() if pdf.pages else ""
                if not first_text:
                    print("   ⚠️  Archivo sin texto (posible imagen/scan). Omitiendo.")
                    continue
                
                bank = detect_bank(first_text)
                print(f"   🏦 Banco detectado: {bank}")
                
                movs = []
                if bank == "GALICIA":
                    movs = parse_galicia_enhanced(pdf)
                elif bank == "BBVA":
                    movs = parse_bbva_enhanced(pdf)
                else:
                    print("   ⚠️  Banco no soportado o no detectado.")
                
                print(f"   ✅ {len(movs)} consumos válidos extraídos.")
                all_movements.extend(movs)
                
        except Exception as e:
            print(f"   ❌ Error al procesar archivo: {e}")
    
    # Exportar resultados mejorados
    if all_movements:
        # Archivo principal
        output_file = "extracted_movements_enhanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_movements, f, indent=4, ensure_ascii=False)
        
        # Archivo separado por monedas
        ars_movements = [m for m in all_movements if m['moneda'] == 'ARS']
        usd_movements = [m for m in all_movements if m['moneda'] == 'USD']
        
        with open("consumos_ars.json", 'w', encoding='utf-8') as f:
            json.dump(ars_movements, f, indent=4, ensure_ascii=False)
        
        with open("consumos_usd.json", 'w', encoding='utf-8') as f:
            json.dump(usd_movements, f, indent=4, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"💾 RESULTADOS MEJORADOS GUARDADOS")
        print('='*80)
        print(f"📁 Archivo principal: {output_file} - Total: {len(all_movements)} consumos")
        print(f"💰 Consumos en ARS: consumos_ars.json - {len(ars_movements)} movimientos")
        print(f"🌎 Consumos en USD: consumos_usd.json - {len(usd_movements)} movimientos")
        
        # Estadísticas mejoradas
        banks = {}
        currencies = {}
        for m in all_movements:
            banks[m['banco']] = banks.get(m['banco'], 0) + 1
            currencies[m['moneda']] = currencies.get(m['moneda'], 0) + 1
        
        print(f"\n📊 ESTADÍSTICAS:")
        for bank, count in banks.items():
            print(f"  🏦 {bank}: {count} consumos")
        for currency, count in currencies.items():
            print(f"  💱 {currency}: {count} consumos")
        
        # Top consumos
        print(f"\n🏆 TOP 10 CONSUMOS (por monto):")
        sorted_movs = sorted(all_movements, key=lambda x: x['monto'], reverse=True)
        for i, m in enumerate(sorted_movs[:10]):
            print(f"  {i+1:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion'][:40]}")
        
    else:
        print("\n⚠️  No se extrajeron consumos válidos.")

if __name__ == "__main__":
    main()