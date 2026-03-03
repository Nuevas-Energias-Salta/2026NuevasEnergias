#!/usr/bin/env python3
"""
Extraer PDF de Banco Macro con OCR mejorado
"""
import os
import subprocess
import json
from datetime import datetime

def extract_with_ocr():
    """Extraer texto usando OCR"""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        # Configurar rutas
        poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        pdf_path = "resumenes/descarga.pdf"
        
        print("Convirtiendo PDF a imagenes...")
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        
        print(f"Procesando {len(images)} pagina(s) con OCR...")
        all_text = []
        
        for i, image in enumerate(images):
            print(f"  Pagina {i+1}...")
            
            # Configuracion optimizada para finanzas
            custom_config = r'--oem 3 --psm 6 -l spa+eng'
            text = pytesseract.image_to_string(image, config=custom_config)
            all_text.append(text)
            
            # Guardar texto de cada pagina para debug
            with open(f"resumenes/pagina_{i+1}_ocr.txt", 'w', encoding='utf-8') as f:
                f.write(text)
        
        combined_text = '\n'.join(all_text)
        
        # Guardar texto completo
        with open("resumenes/macro_ocr_completo.txt", 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        return combined_text
        
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

def parse_movements(text):
    """Parsear movimientos del texto OCR"""
    movements = []
    lines = text.split('\n')
    
    print(f"\nAnalizando {len(lines)} lineas para movimientos...")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Buscar patrones de movimientos
        # Lineas con fechas y montos
        has_date = False
        has_amount = False
        
        # Patrones de fecha
        date_patterns = [
            r'\b\d{2}[/-]\d{2}[/-]?\d{0,2}\b',  # DD/MM o DD/MM/YY
            r'\b\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}\b',  # D/M o D/M/YY
        ]
        
        # Patrones de monto
        amount_patterns = [
            r'\$\s*[\d.,]+',  # $ seguido de numero
            r'\b\d{1,5}[.,]\d{2}\b',  # numero con 2 decimales
            r'USD\s*[\d.,]+',  # USD seguido de numero
        ]
        
        import re
        for pattern in date_patterns:
            if re.search(pattern, line):
                has_date = True
                break
                
        for pattern in amount_patterns:
            if re.search(pattern, line):
                has_amount = True
                break
        
        # Si tiene fecha y monto, es probablemente un movimiento
        if has_date and has_amount:
            movements.append({
                'linea': i+1,
                'texto': line,
                'fecha': None,
                'monto': None,
                'descripcion': line
            })
    
    return movements

def main():
    print("=== EXTRACCION OCR BANCO MACRO ===")
    
    # Extraer con OCR
    text = extract_with_ocr()
    
    if text and len(text.strip()) > 100:
        print(f"\nOK - OCR exitoso! Texto extraido: {len(text)} caracteres")
        
        # Parsear movimientos
        movements = parse_movements(text)
        
        if movements:
            print(f"\nMovimientos encontrados: {len(movements)}")
            for i, mov in enumerate(movements[:10]):
                print(f"  {i+1}: {mov['texto']}")
            
            # Guardar movimientos
            output_json = f"macro_consumos_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"\nOK - Movimientos guardados: {output_json}")
            return True
        else:
            print("\nNo se identificaron movimientos claros")
            
            # Mostrar primeras 20 lineas del texto para analisis
            lines = text.split('\n')
            print("\nPrimeras 20 lineas del OCR:")
            for i, line in enumerate(lines[:20]):
                if line.strip():
                    print(f"  {i+1}: {line}")
    else:
        print("\nX - Error en OCR o texto vacio")
    
    return False

if __name__ == "__main__":
    main()