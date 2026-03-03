# ALTERNATIVAS DE OCR MEJORADAS PARA MACRO BANK

print("EXPLORANDO ALTERNATIVAS DE OCR")
print("="*50)

import sys
import os
import re
import json
from pathlib import Path

def probar_tesseract_ocr():
    """Probar Tesseract OCR como alternativa"""
    print("\n1. PROBANDO TESSERACT OCR...")
    
    try:
        import pytesseract
        from PIL import Image
        import pypdfium2 as pdfium
        
        # Convertir PDF a imágenes para Tesseract
        pdf_path = "resumenes/descarga.pdf"
        pdf = pdfium.PdfDocument(pdf_path)
        
        all_text = ""
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            pil_image = page.render(scale=3).to_pil()  # Mayor resolución
            
            # OCR con Tesseract en español
            text = pytesseract.image_to_string(
                pil_image, 
                lang='spa',
                config='--psm 6 --oem 3'
            )
            all_text += f"\n--- PÁGINA {page_num + 1} ---\n{text}\n"
            print(f"   Página {page_num + 1} procesada...")
        
        pdf.close()
        
        # Guardar resultado
        with open("tesseract_ocr_result.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        
        print("   ✓ Tesseract OCR completado")
        print("   ✓ Guardado en tesseract_ocr_result.txt")
        return all_text
        
    except ImportError:
        print("   ❌ Tesseract no disponible. Instalar con: pip install pytesseract")
        print("   ❌ Y instalar Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
        return None
    except Exception as e:
        print(f"   ❌ Error con Tesseract: {e}")
        return None

def probar_paddleocr():
    """Probar PaddleOCR como alternativa"""
    print("\n2. PROBANDO PADDLEOCR...")
    
    try:
        from paddleocr import PaddleOCR
        import pypdfium2 as pdfium
        
        # Inicializar PaddleOCR para español
        ocr = PaddleOCR(use_angle_cls=True, lang='es')
        
        pdf_path = "resumenes/descarga.pdf"
        pdf = pdfium.PdfDocument(pdf_path)
        
        all_text = ""
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            pil_image = page.render(scale=3).to_pil()
            
            # OCR con PaddleOCR
            result = ocr.ocr(pil_image, cls=True)
            
            # Extraer texto
            page_text = ""
            for line in result:
                for word_info in line:
                    text = word_info[1][0]
                    page_text += text + " "
            
            all_text += f"\n--- PÁGINA {page_num + 1} ---\n{page_text}\n"
            print(f"   Página {page_num + 1} procesada...")
        
        pdf.close()
        
        # Guardar resultado
        with open("paddle_ocr_result.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        
        print("   ✓ PaddleOCR completado")
        print("   ✓ Guardado en paddle_ocr_result.txt")
        return all_text
        
    except ImportError:
        print("   ❌ PaddleOCR no disponible. Instalar con: pip install paddleocr")
        return None
    except Exception as e:
        print(f"   ❌ Error con PaddleOCR: {e}")
        return None

def probar_google_vision():
    """Probar Google Cloud Vision OCR (requiere API key)"""
    print("\n3. GOOGLE CLOUD VISION OCR...")
    print("   Requiere Google Cloud Vision API key")
    
    api_key = input("   Ingresa tu Google Vision API key (o presiona Enter para saltar): ").strip()
    if not api_key:
        print("   Saltando Google Vision...")
        return None
    
    try:
        import base64
        import requests
        from google.cloud import vision
        from PIL import Image
        import io
        
        # Convertir primera página a imagen
        pdf_path = "resumenes/descarga.pdf"
        pdf = pypdfium2.PdfDocument(pdf_path)
        page = pdf[0]
        pil_image = page.render(scale=2).to_pil()
        
        # Convertir imagen a base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        image_content = base64.b64encode(buffered.getvalue()).decode()
        
        # Llamar a Google Vision API
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        request_body = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {"type": "TEXT_DETECTION", "maxResults": 10},
                        {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 10}
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=request_body)
        
        if response.status_code == 200:
            result = response.json()
            text = result["responses"][0]["fullTextAnnotation"]["text"]
            
            with open("google_vision_ocr.txt", "w", encoding="utf-8") as f:
                f.write(text)
            
            print("   ✓ Google Vision OCR completado")
            print("   ✓ Guardado en google_vision_ocr.txt")
            return text
        else:
            print(f"   ❌ Error en API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error con Google Vision: {e}")
        return None

def probar_mejor_imagen():
    """Mejorar la imagen PDF antes de OCR"""
    print("\n4. MEJORAR IMÁGEN ANTES DE OCR...")
    
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import pypdfium2 as pdfium
        
        pdf_path = "resumenes/descarga.pdf"
        pdf = pdfium.PdfDocument(pdf_path)
        page = pdf[0]
        original_image = page.render(scale=4).to_pil()  # Alta resolución
        
        # Mejoras de imagen
        # 1. Convertir a escala de grises
        gray_image = original_image.convert('L')
        
        # 2. Mejorar contraste
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(2.0)
        
        # 3. Mejorar nitidez
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        sharpened_image = enhancer.enhance(2.0)
        
        # 4. Reducir ruido
        denoised_image = sharpened_image.filter(ImageFilter.MedianFilter(size=1))
        
        # Guardar imagen mejorada
        denoised_image.save("mejor_imagen_macro.png")
        
        # Probar EasyOCR con imagen mejorada
        import easyocr
        reader = easyocr.Reader(['es'], gpu=False)
        result = reader.readtext(denoised_image, detail=0, paragraph=True)
        
        improved_text = "\n".join(result)
        
        with open("easyocr_mejorado.txt", "w", encoding="utf-8") as f:
            f.write(improved_text)
        
        print("   ✓ Imagen mejorada guardada en mejor_imagen_macro.png")
        print("   ✓ OCR con imagen mejorada completado")
        print("   ✓ Guardado en easyocr_mejorado.txt")
        return improved_text
        
    except Exception as e:
        print(f"   ❌ Error mejorando imagen: {e}")
        return None

def main():
    """Función principal para probar alternativas OCR"""
    
    print("ALTERNATIVAS DE OCR PARA MEJORAR EXTRACCIÓN DE MACRO BANK")
    print("="*70)
    print("\nPROBLEMA ACTUAL:")
    print("- EasyOCR no reconoce bien los caracteres en resúmenes bancarios")
    print("- Errores comunes: HRTEL -> MARTEL, montos incorrectos, etc.")
    print("\nSOLUCIONES PROPUESTAS:")
    
    # Probar alternativas
    tesseract_result = probar_tesseract_ocr()
    paddle_result = probar_paddleocr()
    google_result = probar_google_vision()
    improved_result = probar_mejor_imagen()
    
    print("\n" + "="*70)
    print("RESUMEN DE ALTERNATIVAS PROBADAS:")
    print("="*70)
    
    results = {
        "EasyOCR (actual)": "extracted_movements_enhanced.json",
        "Tesseract": "tesseract_ocr_result.txt" if tesseract_result else None,
        "PaddleOCR": "paddle_ocr_result.txt" if paddle_result else None,
        "Google Vision": "google_vision_ocr.txt" if google_result else None,
        "EasyOCR + Mejora": "easyocr_mejorado.txt" if improved_result else None
    }
    
    for method, archivo in results.items():
        if archivo:
            print(f"✅ {method}: {archivo}")
        else:
            print(f"❌ {method}: No disponible")
    
    print(f"\nRECOMENDACIÓN:")
    print(f"1. Probar Google Vision API (más preciso pero requiere clave)")
    print(f"2. Probar imagen mejorada + EasyOCR (gratis y más efectivo)")
    print(f"3. Probar PaddleOCR (alternativa open source)")

if __name__ == "__main__":
    main()