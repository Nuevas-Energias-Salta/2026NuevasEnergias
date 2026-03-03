#!/usr/bin/env python3
"""
Extracción de datos de PDF de Banco Macro usando OCR
"""
import subprocess
import os
import json
import re
from datetime import datetime

def setup_poppler_path():
    """
    Configura la ruta de Poppler en Windows
    """
    # Ruta común donde se instala Poppler en Windows
    poppler_paths = [
        r"C:\Program Files\poppler-24.02.0\Library\bin",
        r"C:\Program Files\poppler\bin", 
        r"C:\poppler-24.02.0\Library\bin",
        r"C:\tools\poppler\bin"
    ]
    
    for path in poppler_paths:
        if os.path.exists(path):
            os.environ['PATH'] += os.pathsep + path
            print(f"Poppler encontrado en: {path}")
            return True
    
    print("Poppler no encontrado. Descarga e instala desde:")
    print("https://github.com/oschwartz10612/poppler-windows/releases/")
    return False

def extract_with_ocr(pdf_path):
    """
    Extrae texto usando OCR
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        # Configurar pytesseract para Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        print("Convirtiendo PDF a imágenes para OCR...")
        images = convert_from_path(pdf_path, dpi=300)
        
        all_text = []
        for i, image in enumerate(images):
            print(f"Procesando página {i+1} con OCR...")
            
            # Usar español y configuración optimizada para finanzas
            text = pytesseract.image_to_string(
                image, 
                lang='spa',
                config='--psm 6 --oem 3'
            )
            all_text.append(text)
        
        full_text = '\n'.join(all_text)
        return full_text
        
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

def extract_with_external_tools(pdf_path):
    """
    Intenta usar herramientas externas como ABBYY o Adobe si están disponibles
    """
    # Método alternativo usando python-pdfparser2
    try:
        import pdfplumber
        
        print("Intentando con pdfplumber...")
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
            
            if all_text.strip():
                return all_text
                
    except ImportError:
        print("pdfplumber no disponible")
    except Exception as e:
        print(f"Error con pdfplumber: {e}")
    
    return None

def parse_macro_movements(text):
    """
    Parsea movimientos del texto extraído
    """
    movements = []
    lines = text.split('\n')
    
    # Patrones para Banco Macro
    patterns = {
        'date': r'(\d{2}[/-]\d{2}[/-]\d{2,4})',
        'amount': r'\$?\s*[\d.,]+',
        'consumo': r'CONSUMO|COMPRA|PAGO',
    }
    
    for i, line in enumerate(lines):
        line = line.strip().upper()
        if not line:
            continue
            
        # Buscar líneas con fechas y montos
        if re.search(patterns['date'], line) and re.search(patterns['amount'], line):
            # Extraer componentes
            date_match = re.search(patterns['date'], line)
            amount_matches = re.findall(patterns['amount'], line)
            
            if date_match and amount_matches:
                movement = {
                    'fecha': date_match.group(1),
                    'descripcion': line[:date_match.start()].strip() + ' ' + line[date_match.end():].strip(),
                    'monto': amount_matches[-1] if amount_matches else '',
                    'linea_original': line,
                    'linea_numero': i+1
                }
                movements.append(movement)
    
    return movements

def main():
    pdf_path = "resumenes/descarga.pdf"
    
    print("=== EXTRACCIÓN DE DATOS BANCO MACRO ===")
    
    # Configurar Poppler
    setup_poppler_path()
    
    # Método 1: Intentar extracción directa
    print("\n1. Intentando extracción directa con pdftotext...")
    try:
        result = subprocess.run(['pdftotext', '-layout', pdf_path, 'temp_direct.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            with open('temp_direct.txt', 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                print("Extracción directa exitosa")
            else:
                print("Extracción directa sin contenido")
    except:
        print("Error en extracción directa")
    
    # Método 2: pdfplumber
    print("\n2. Intentando con pdfplumber...")
    text = extract_with_external_tools(pdf_path)
    
    # Método 3: OCR si todo lo demás falla
    if not text or not text.strip():
        print("\n3. Intentando con OCR...")
        text = extract_with_ocr(pdf_path)
    
    if text and text.strip():
        print(f"\nTexto extraído: {len(text)} caracteres")
        
        # Guardar texto completo
        with open('macro_texto_extraido.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Parsear movimientos
        movements = parse_macro_movements(text)
        
        print(f"\nMovimientos encontrados: {len(movements)}")
        for i, mov in enumerate(movements[:5]):
            print(f"{i+1}: {mov}")
        
        # Guardar movimientos
        if movements:
            output_file = f"macro_consumos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            print(f"Movimientos guardados en: {output_file}")
    else:
        print("\nNo se pudo extraer texto del PDF")
        print("Recomendaciones:")
        print("1. Verifica que el PDF no esté protegido con contraseña")
        print("2. Intenta abrir el PDF manualmente y verificar si tiene contenido")
        print("3. Considera usar un escaneo de mayor calidad")

if __name__ == "__main__":
    main()