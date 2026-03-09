#!/usr/bin/env python3
"""
Extraer datos del PDF de Banco Macro - Convertir a imagen primero
"""
import os
import subprocess
import json
from datetime import datetime

def convert_pdf_to_images():
    """Convertir PDF a imágenes usando Poppler"""
    try:
        from pdf2image import convert_from_path
        
        poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
        pdf_path = "resumenes/descarga.pdf"
        
        print("Convirtiendo PDF a imágenes...")
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        
        print(f"Convertidas {len(images)} páginas a imágenes")
        
        # Guardar imágenes para revisión
        for i, image in enumerate(images):
            image_path = f"resumenes/pagina_{i+1}.png"
            image.save(image_path)
            print(f"Guardada: {image_path}")
        
        return images
        
    except Exception as e:
        print(f"Error al convertir: {e}")
        return None

def extract_text_from_images():
    """Extraer texto de imágenes con OCR (si está disponible)"""
    try:
        import pytesseract
        
        # Intentar con ruta por defecto
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        ]
        
        tesseract_found = False
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                tesseract_found = True
                print(f"Tesseract encontrado: {path}")
                break
        
        if not tesseract_found:
            print("Tesseract no encontrado")
            return None
        
        # Procesar imágenes guardadas
        all_text = []
        
        for i in range(1, 10):  # Máximo 10 páginas
            image_path = f"resumenes/pagina_{i}.png"
            if os.path.exists(image_path):
                print(f"Procesando {image_path}...")
                
                from PIL import Image
                image = Image.open(image_path)
                
                # Extraer texto en español
                text = pytesseract.image_to_string(image, lang='spa')
                all_text.append(text)
                
                print(f"  Texto extraído: {len(text)} caracteres")
            else:
                break
        
        if all_text:
            combined_text = '\n\n'.join(all_text)
            return combined_text
        
    except ImportError:
        print("pytesseract no disponible. Instalar con: pip install pytesseract")
    except Exception as e:
        print(f"Error en OCR: {e}")
    
    return None

def simple_pdf_info():
    """Obtener información básica del PDF"""
    poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
    pdf_path = "resumenes/descarga.pdf"
    
    env = os.environ.copy()
    env['PATH'] = poppler_path + os.pathsep + env.get('PATH', '')
    
    try:
        # Usar pdfinfo para obtener información
        cmd = ['pdfinfo', pdf_path]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        
        print("=== INFORMACIÓN DEL PDF ===")
        print(result.stdout)
        
        # Intentar extraer texto de nuevo con diferentes opciones
        print("\n=== INTENTANDO OTRAS OPCIONES ===")
        
        methods = [
            ("-nopgbrk", "sin saltos de página"),
            ("-enc Latin1", "codificación Latin1"),
            ("-fixed 2", "ancho fijo")
        ]
        
        for option, desc in methods:
            try:
                output = f"resumenes/prueba_{option.replace(' ', '_')}.txt"
                cmd = ['pdftotext'] + option.split() + [pdf_path, output]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
                
                if result.returncode == 0 and os.path.exists(output):
                    with open(output, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    lines = [line for line in content.split('\n') if line.strip()]
                    print(f"{desc}: {len(lines)} líneas")
                    
                    if len(lines) > 5:
                        print(f"  Primeras líneas:")
                        for i, line in enumerate(lines[:3]):
                            print(f"    {i+1}: {line}")
            except:
                pass
                
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=== ANÁLISIS PDF BANCO MACRO ===")
    
    # 1. Obtener información del PDF
    simple_pdf_info()
    
    # 2. Convertir a imágenes para revisión
    print("\n" + "="*50)
    images = convert_pdf_to_images()
    
    if images:
        print("\n✓ Imágenes generadas. Revisa los archivos PNG en 'resumenes'")
        print("Puedes abrir las imágenes para ver el contenido manualmente")
        
        # 3. Intentar OCR si está disponible
        print("\n" + "="*50)
        text = extract_text_from_images()
        
        if text and len(text.strip()) > 100:
            print(f"\n✓ OCR exitoso!")
            
            # Guardar texto
            with open("resumenes/macro_texto_ocr.txt", 'w', encoding='utf-8') as f:
                f.write(text)
            
            print("Texto guardado en: resumenes/macro_texto_ocr.txt")
            
            # Buscar líneas con números y $
            lines = text.split('\n')
            potential_movements = []
            
            for line in lines:
                line = line.strip()
                if any(char.isdigit() for char in line) and ('$' in line or 'USD' in line):
                    potential_movements.append(line)
            
            if potential_movements:
                print(f"\nMovimientos potenciales: {len(potential_movements)}")
                for i, mov in enumerate(potential_movements[:10]):
                    print(f"  {i+1}: {mov}")
        else:
            print("\nOCR no disponible o sin resultados")
            print("Instala Tesseract OCR para extracción automática")
    
    print("\n" + "="*50)
    print("RESUMEN:")
    print("1. Si hay imágenes PNG: abre resumenes/pagina_1.png para ver contenido")
    print("2. Si quieres OCR automático: instala Tesseract OCR")
    print("3. Luego ejecuta: python extraer_con_ocr.py")

if __name__ == "__main__":
    main()