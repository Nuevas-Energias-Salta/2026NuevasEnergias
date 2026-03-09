#!/usr/bin/env python3
"""
OCR mejorado para capturar TODOS los movimientos de Banco Macro
"""
import os
import json
from datetime import datetime

def extract_comprehensive_ocr():
    """OCR con configuración optimizada para capturar todos los datos"""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image, ImageEnhance, ImageFilter
        
        # Configurar rutas
        poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        pdf_path = "resumenes/descarga.pdf"
        
        print("Convirtiendo PDF a imagenes de alta calidad...")
        images = convert_from_path(pdf_path, dpi=400, poppler_path=poppler_path)
        
        all_text_pages = []
        
        for i, image in enumerate(images):
            print(f"\n=== PROCESANDO PÁGINA {i+1} ===")
            
            # Mejorar imagen para mejor OCR
            # 1. Convertir a escala de grises
            gray = image.convert('L')
            
            # 2. Aumentar contraste
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2.0)
            
            # 3. Aplicar umbral para hacer texto más nítido
            threshold = 128
            binary = enhanced.point(lambda x: 0 if x < threshold else 255, '1')
            
            # 4. Guardar imagen mejorada para debug
            binary.save(f"resumenes/pagina_{i+1}_mejorada.png")
            
            # 5. Extraer texto con múltiples configuraciones
            configs = [
                r'--oem 3 --psm 6 -l spa+eng',  # Configuración estándar
                r'--oem 3 --psm 4 -l spa+eng',  # Asumir una columna
                r'--oem 3 --psm 11 -l spa+eng', # Texto denso
                r'--oem 3 --psm 3 -l spa+eng',  # Página completamente automática
            ]
            
            best_text = ""
            best_length = 0
            
            for j, config in enumerate(configs):
                try:
                    text = pytesseract.image_to_string(binary, config=config)
                    
                    print(f"  Config {j+1}: {len(text)} caracteres")
                    
                    if len(text) > best_length:
                        best_length = len(text)
                        best_text = text
                
                except Exception as e:
                    print(f"  Error config {j+1}: {e}")
            
            # Guardar mejor resultado de esta página
            with open(f"resumenes/pagina_{i+1}_completa.txt", 'w', encoding='utf-8') as f:
                f.write(best_text)
            
            all_text_pages.append(best_text)
            
            print(f"  Mejor resultado: {len(best_text)} caracteres")
        
        # Combinar todo el texto
        full_text = '\n\n'.join(all_text_pages)
        
        # Guardar texto completo
        with open("resumenes/macro_ocr_completo_mejorado.txt", 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        return full_text
        
    except Exception as e:
        print(f"Error en OCR mejorado: {e}")
        return None

def find_all_movements(text):
    """
    Busca TODOS los movimientos usando múltiples patrones
    """
    movements = []
    lines = text.split('\n')
    
    print(f"\nAnalizando {len(lines)} líneas para encontrar movimientos...")
    
    # Patrones más amplios para detectar movimientos
    import re
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Patrones para diferentes formatos de movimiento
        patterns = [
            # Formato 1: Fecha + Descripción + Monto
            r'^\d{1,2}\s+\w+\s+\d{2,4}.*[\d.,]+$',  # 21 Enero 26 ... 1234,56
            
            # Formato 2: Cualquier línea con fecha y monto
            r'.*\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}.*[\d.,]+\s*$',  # ...21/01/26...1234,56
            
            # Formato 3: Línea con números grandes (montos)
            r'.*\b\d{1,5}[.,]\d{2}\s*$',  # ...1234,56
            
            # Formato 4: Línea con $
            r'.*\$.*\d',  # ...$1234...
            
            # Formato 5: Línea con USD
            r'.*USD.*\d',  # ...USD1234...
            
            # Formato 6: Línea con patrones de tarjeta/consumo
            r'.*\d{6,}.*\d{1,5}[.,]\d{2}\s*$',  # ...123456...1234,56
        ]
        
        is_movement = False
        matched_pattern = None
        
        for pattern in patterns:
            if re.search(pattern, line):
                is_movement = True
                matched_pattern = pattern
                break
        
        if is_movement:
            # Filtrar líneas que probablemente no son movimientos
            exclude_keywords = [
                'RESUMEN', 'PÁGINA', 'TARJETA', 'CUENTA', 'SALDO', 
                'LÍMITE', 'PAGO MÍNIMO', 'PAGO TOTAL', 'VENCIMIENTO',
                'ESTADO DE CUENTA', 'SUCURSAL', 'BANCO MACRO'
            ]
            
            exclude = any(keyword in line.upper() for keyword in exclude_keywords)
            
            if not exclude:
                movements.append({
                    'linea': i+1,
                    'texto': line,
                    'patron': matched_pattern
                })
    
    print(f"Movimientos potenciales encontrados: {len(movements)}")
    return movements

def main():
    print("=== OCR COMPLETO BANCO MACRO - TODAS LAS TARJETAS ===")
    
    # Extracción OCR mejorada
    text = extract_comprehensive_ocr()
    
    if text and len(text.strip()) > 100:
        print(f"\nOK - OCR completo: {len(text)} caracteres")
        
        # Buscar todos los movimientos
        movements = find_all_movements(text)
        
        if movements:
            print(f"\n=== MOVIMIENTOS ENCONTRADOS: {len(movements)} ===")
            
            # Mostrar primeros 20 movimientos
            for i, movement in enumerate(movements[:20]):
                print(f"{i+1:2}: {movement['texto']}")
            
            if len(movements) > 20:
                print(f"... y {len(movements) - 20} movimientos más")
            
            # Guardar todos los movimientos
            output_json = f"macro_todos_movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"\nTodos los movimientos guardados en: {output_json}")
            
            # Categorización por tarjeta si es posible
            print("\n=== ANÁLISIS POR TARJETA ===")
            
            # Buscar números de tarjeta o patrones
            card_patterns = [
                r'\b\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4}\b',  # 16 dígitos
                r'\*\d{4,}',  # *1234
                r'TARJETA\s+\w+',  # TARJETA VISA
                r'\*\*\*\*?\s*\d{4,}',  # ****1234
            ]
            
            import re
            cards_found = set()
            
            for movement in movements:
                text = movement['texto']
                for pattern in card_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        cards_found.add(match.group())
            
            if cards_found:
                print("Posibles tarjetas identificadas:")
                for card in cards_found:
                    print(f"  - {card}")
            else:
                print("No se identificaron tarjetas específicas")
        else:
            print("\nNo se encontraron movimientos")
    else:
        print("\nError en OCR")

if __name__ == "__main__":
    main()