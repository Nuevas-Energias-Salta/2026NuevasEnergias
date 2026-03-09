#!/usr/bin/env python3
"""
Extraer PDF de Banco Macro con OCR
"""
import os
import subprocess
import json
from datetime import datetime

def setup_tesseract():
    """Configurar ruta de Tesseract"""
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Gonza\AppData\Local\Tesseract-OCR\tesseract.exe"
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            print(f"Tesseract encontrado: {path}")
            return path
    
    print("Tesseract no encontrado. Por favor instálalo desde:")
    print("https://github.com/UB-Mannheim/tesseract/wiki")
    return None

def extract_with_ocr(pdf_path):
    """Extraer texto usando OCR"""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        # Configurar rutas
        poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
        tesseract_path = setup_tesseract()
        
        if not tesseract_path:
            return None
            
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        print("Convirtiendo PDF a imágenes...")
        images = convert_from_path(
            pdf_path, 
            dpi=300,
            poppler_path=poppler_path
        )
        
        print(f"Procesando {len(images)} página(s) con OCR...")
        all_text = []
        
        for i, image in enumerate(images):
            print(f"  Página {i+1}...")
            
            # Configuración optimizada para finanzas
            custom_config = r'--oem 3 --psm 6 -l spa+eng'
            text = pytesseract.image_to_string(image, config=custom_config)
            all_text.append(text)
        
        return '\n'.join(all_text)
        
    except ImportError as e:
        print(f"Faltan dependencias: {e}")
        print("Instalar con: pip install pytesseract pdf2image")
        return None
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

def parse_movements(text):
    """Parsear movimientos del texto OCR"""
    movements = []
    lines = text.split('\n')
    
    # Patrones mejorados para Banco Macro
    import re
    
    for i, line in enumerate(lines):
        line = line.strip().upper()
        if not line:
            continue
        
        # Buscar patrones de movimientos
        # Fechas: DD/MM o DD/MM/YY
        if re.search(r'\d{2}[/-]\d{2}[/-]?\d{0,2}', line):
            # Montos: con $ o números grandes
            if '$' in line or re.search(r'\b\d{1,5}[.,]\d{2}\b', line):
                movements.append({
                    'linea': i+1,
                    'texto': line,
                    'fecha': None,
                    'monto': None,
                    'descripcion': line
                })
    
    return movements

def main():
    print("=== EXTRACCIÓN CON OCR - BANCO MACRO ===")
    
    pdf_path = "resumenes/descarga.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF no encontrado: {pdf_path}")
        return
    
    # Extraer con OCR
    text = extract_with_ocr(pdf_path)
    
    if text and len(text.strip()) > 100:
        print(f"\n✓ OCR exitoso! Texto extraído: {len(text)} caracteres")
        
        # Guardar texto completo
        with open("resumenes/macro_ocr_completo.txt", 'w', encoding='utf-8') as f:
            f.write(text)
        
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
            
            print(f"\n✓ Movimientos guardados: {output_json}")
        else:
            print("\nNo se identificaron movimientos claros")
            print("Revisa el archivo: resumenes/macro_ocr_completo.txt")
    else:
        print("\n✗ Error en OCR")
        print("Verifica que Tesseract esté instalado correctamente")

if __name__ == "__main__":
    main()