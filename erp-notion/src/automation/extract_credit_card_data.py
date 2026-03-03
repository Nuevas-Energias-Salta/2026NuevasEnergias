import pdfplumber
import re
import json
import os
import sys
import io
from datetime import datetime

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def detect_bank(text):
    """Detecta el banco basado en palabras clave en el texto del PDF"""
    if "BBVA" in text.upper() or "AVBB" in text.upper() or "BANCO BBVA" in text.upper():
        return "BBVA"
        
    if "GALICIA" in text.upper() or "BANCO GALICIA" in text.upper():
        return "GALICIA"
        
    if "VISA BUSINESS" in text.upper():
        return "GALICIA"
    
    return "DESCONOCIDO"

def parse_galicia(pdf):
    """
    Parsea resumen de Galicia Visa Business
    SOLO extrae de la sección DETALLE DEL CONSUMO
    Incluye todas las tarjetas, impuestos y comisiones
    """
    movements = []
    
    print("   -> Procesando formato GALICIA...")
    print("   -> Extrayendo SOLO de sección 'DETALLE DEL CONSUMO'...")
    
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        in_detalle_section = False
        
        for line in lines:
            # Detectar inicio de sección
            if "DETALLE DEL CONSUMO" in line.upper():
                in_detalle_section = True
                print(f"   -> ✓ Encontrada sección DETALLE DEL CONSUMO")
                continue
            
            # Detectar fin de sección - SOLO "TOTAL A PAGAR"
            if in_detalle_section and "TOTAL A PAGAR" in line.upper():
                print(f"   -> ✓ Fin de sección DETALLE DEL CONSUMO (TOTAL A PAGAR)")
                in_detalle_section = False
                continue
            
            # Solo procesar líneas dentro de la sección
            if not in_detalle_section:
                continue
            
            # Ignorar encabezado de columnas
            if "FECHA" in line and "REFERENCIA" in line and "COMPROBANTE" in line:
                continue
            
            # Ignorar líneas de totales por tarjeta (solo informativos)
            if "Total Consumos de" in line:
                print(f"      ℹ️  Subtotal tarjeta: {line[:60]}...")
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
                # Buscar patrón: X.XXX,XX o XXX,XX
                if ',' in token and re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', token):
                    try:
                        monto_clean = token.replace('.', '').replace(',', '.')
                        monto_val = abs(float(monto_clean))
                        break
                    except:
                        continue
            
            if monto_val is None:
                print(f"      ⚠️  No se pudo extraer monto: {line[:70]}...")
                continue
            
            # Extraer descripción (limpieza básica)
            desc = resto
            # Quitar letra inicial (K, F, E, * etc)
            desc = re.sub(r'^[A-Z*]\s+', '', desc)
            # Quitar USD si está
            if "USD" in desc:
                desc = desc.split("USD")[0]
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
            
            # Guardar movimiento
            movements.append({
                "fecha": fecha_str,
                "descripcion": desc,
                "monto": monto_val,
                "moneda": moneda,
                "banco": "GALICIA",
                "original": line
            })
    
    return movements

def parse_bbva(pdf):
    """Parsea resumen BBVA"""
    movements = []
    print("   -> Procesando formato BBVA...")
    
    meses = {
        "Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Ago": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"
    }
    
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        for line in lines:
            # Patrón BBVA: DD-MMM-YY (ej: 06-Ago-25)
            match = re.search(r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$', line)
            if match:
                dd = match.group(1)
                mm_str = match.group(2)
                yy = match.group(3)
                resto = match.group(4)
                
                mm = meses.get(mm_str.title(), "00")
                fecha_fmt = f"{dd}-{mm}-{yy}"
                
                tokens = resto.split()
                if len(tokens) < 2:
                    continue
                
                # Verificar si es monto
                def is_monto(s):
                    return re.match(r'^-?[\d.,]+$', s) and (',' in s or '.' in s)
                
                last = tokens[-1]
                second_last = tokens[-2] if len(tokens) > 1 else ""
                
                val_str = last
                if not is_monto(val_str) and is_monto(second_last):
                    val_str = second_last
                
                if not is_monto(val_str):
                    continue
                
                try:
                    monto_final = float(val_str.replace('.', '').replace(',', '.'))
                except:
                    continue
                
                # Descripción
                desc_tokens = tokens[:-1]
                while desc_tokens and (is_monto(desc_tokens[-1]) or re.match(r'^\d+$', desc_tokens[-1].replace('.', ''))):
                    desc_tokens.pop()
                
                if desc_tokens and (re.match(r'\d+', desc_tokens[-1]) or "C." in desc_tokens[-1]):
                    desc_tokens.pop()
                if desc_tokens and (re.match(r'\d+', desc_tokens[-1]) or "C." in desc_tokens[-1]):
                    desc_tokens.pop()
                
                desc = " ".join(desc_tokens)
                
                # Filtros
                keywords_to_ignore = ["SU PAGO EN", "SALDO ANTERIOR", "PAGO DE RESUMEN"]
                if any(k in desc.upper() for k in keywords_to_ignore):
                    continue
                
                movements.append({
                    "fecha": fecha_fmt,
                    "descripcion": desc,
                    "monto": abs(monto_final),
                    "moneda": "ARS",
                    "banco": "BBVA",
                    "original": line
                })
    
    return movements

def main():
    folder = "resumenes"
    if not os.path.exists(folder):
        print(f"Carpeta {folder} no encontrada.")
        return
    
    files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    all_movements = []
    
    print(f"Encontrados {len(files)} archivos PDF.\n")
    
    for filename in files:
        path = os.path.join(folder, filename)
        print(f"\n{'='*70}")
        print(f"Procesando: {filename}")
        print('='*70)
        
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
                    movs = parse_galicia(pdf)
                elif bank == "BBVA":
                    movs = parse_bbva(pdf)
                else:
                    print("   ⚠️  Banco no soportado o no detectado.")
                
                print(f"   ✓ {len(movs)} movimientos extraídos.")
                all_movements.extend(movs)
                
        except Exception as e:
            print(f"   ❌ Error al procesar archivo: {e}")
    
    # Exportar resultados
    if all_movements:
        output_file = "extracted_movements.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_movements, f, indent=4, ensure_ascii=False)
        print(f"\n{'='*70}")
        print(f"💾 Guardado en {output_file} - Total: {len(all_movements)} movimientos")
        print('='*70)
        
        # Estadísticas
        galicia_count = len([m for m in all_movements if m['banco'] == 'GALICIA'])
        bbva_count = len([m for m in all_movements if m['banco'] == 'BBVA'])
        ars_count = len([m for m in all_movements if m['moneda'] == 'ARS'])
        usd_count = len([m for m in all_movements if m['moneda'] == 'USD'])
        
        print(f"\nEstadísticas:")
        print(f"  - Galicia: {galicia_count} movimientos")
        print(f"  - BBVA: {bbva_count} movimientos")
        print(f"  - ARS: {ars_count} movimientos")
        print(f"  - USD: {usd_count} movimientos")
        
        # Preview
        print("\n--- PRIMEROS 5 MOVIMIENTOS ---")
        for m in all_movements[:5]:
            print(f"{m['fecha']} | {m['moneda']:3} {m['monto']:10.2f} | {m['descripcion'][:40]}")
    else:
        print("\n⚠️  No se extrajeron movimientos.")

if __name__ == "__main__":
    main()
