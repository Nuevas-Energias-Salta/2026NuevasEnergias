#!/usr/bin/env python3
"""
Diagnóstico y extracción avanzada de PDF de Banco Macro
"""
import subprocess
import os
import json
import re
from datetime import datetime

def diagnose_pdf(pdf_path):
    """
    Diagnostica el PDF y prueba diferentes métodos de extracción
    """
    print(f"=== DIAGNÓSTICO DEL PDF: {pdf_path} ===")
    
    # Verificar si el archivo existe y su tamaño
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"Tamaño del archivo: {size} bytes")
    else:
        print("El archivo no existe")
        return
    
    # Probar diferentes métodos de extracción
    methods = [
        ("Básico", ['pdftotext', pdf_path]),
        ("Con Layout", ['pdftotext', '-layout', pdf_path]),
        ("Con Tabla", ['pdftotext', '-table', pdf_path]),
        ("Raw", ['pdftotext', '-raw', pdf_path]),
        ("Simple", ['pdftotext', '-simple', pdf_path]),
    ]
    
    for method_name, cmd_base in methods:
        print(f"\n--- Probando método: {method_name} ---")
        output_file = f"resumenes/descarga_{method_name.lower().replace(' ', '_')}.txt"
        cmd = cmd_base + [output_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                # Leer el archivo generado
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    lines = [line for line in content.split('\n') if line.strip()]
                    print(f"OK - {len(lines)} líneas extraídas")
                    
                    if lines:
                        print("Primeras 3 líneas:")
                        for i, line in enumerate(lines[:3]):
                            print(f"  {i+1}: {repr(line)}")
                    else:
                        print("  (Sin contenido visible)")
                else:
                    print("X - No se generó archivo de salida")
            else:
                print(f"X - Error: {result.stderr}")
                
        except Exception as e:
            print(f"X - Excepción: {e}")

def try_ocr_fallback(pdf_path):
    """
    Intenta usar OCR como fallback
    """
    print(f"\n=== INTENTANDO OCR COMO ALTERNATIVA ===")
    
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        print("Convirtiendo PDF a imágenes...")
        images = convert_from_path(pdf_path, dpi=300)
        
        all_text = []
        for i, image in enumerate(images):
            print(f"Procesando página {i+1}...")
            text = pytesseract.image_to_string(image, lang='spa')
            all_text.append(text)
        
        full_text = '\n'.join(all_text)
        
        # Guardar resultado OCR
        with open('resumenes/descarga_ocr.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print("Texto OCR guardado en: resumenes/descarga_ocr.txt")
        
        # Mostrar primeras líneas
        lines = [line for line in full_text.split('\n') if line.strip()][:10]
        if lines:
            print("Primeras líneas del OCR:")
            for i, line in enumerate(lines):
                print(f"  {i+1}: {line}")
        
        return full_text
        
    except ImportError:
        print("pytesseract o pdf2image no disponibles. Instalar con:")
        print("pip install pytesseract pdf2image")
        print("También necesitas Tesseract OCR instalado")
        return None
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

def main():
    pdf_path = "resumenes/descarga.pdf"
    
    # Diagnóstico completo
    diagnose_pdf(pdf_path)
    
    # Intentar OCR si todo lo demás falla
    ocr_text = try_ocr_fallback(pdf_path)
    
    if ocr_text:
        print("\n=== EXTRACCIÓN CON OCR EXITOSA ===")
        print("Ahora podemos procesar este texto para extraer los movimientos")

if __name__ == "__main__":
    main()