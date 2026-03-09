#!/usr/bin/env python3
"""
Procesar imagen de consumos de Banco Macro directamente
"""
import os
import json
import re
from datetime import datetime

def process_image_with_ocr():
    """
    Procesar la imagen de consumos directamente
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
        
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        image_path = "resumenes/image.png"
        
        if not os.path.exists(image_path):
            print(f"No se encuentra la imagen: {image_path}")
            return None
        
        print(f"Procesando imagen: {image_path}")
        
        # Abrir y mejorar la imagen
        image = Image.open(image_path)
        
        print(f"Dimensiones originales: {image.size}")
        
        # Convertir a escala de grises
        gray = image.convert('L')
        
        # Mejorar contraste
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.5)
        
        # Nitidez
        enhancer_sharp = ImageEnhance.Sharpness(enhanced)
        sharpened = enhancer_sharp.enhance(2.0)
        
        # Guardar imagen mejorada
        improved_path = "resumenes/image_mejorada.png"
        sharpened.save(improved_path)
        print(f"Imagen mejorada guardada: {improved_path}")
        
        # Extraer texto con múltiples configuraciones
        configs = [
            r'--oem 3 --psm 6 -l spa+eng',  # Bloque de texto uniforme
            r'--oem 3 --psm 4 -l spa+eng',  # Una columna
            r'--oem 3 --psm 11 -l spa+eng', # Texto denso
            r'--oem 3 --psm 3 -l spa+eng',  # Automático completo
            r'--oem 3 --psm 1 -l spa+eng',  # Solo OCR con OSD
        ]
        
        all_texts = []
        
        for i, config in enumerate(configs):
            try:
                print(f"\nConfiguración {i+1}: {config}")
                text = pytesseract.image_to_string(sharpened, config=config)
                print(f"  Caracteres extraídos: {len(text)}")
                
                all_texts.append(text)
                
                # Guardar cada configuración
                with open(f"resumenes/image_config_{i+1}.txt", 'w', encoding='utf-8') as f:
                    f.write(text)
                
            except Exception as e:
                print(f"  Error: {e}")
        
        # Seleccionar el mejor resultado (más caracteres)
        best_text = max(all_texts, key=len) if all_texts else ""
        
        # Guardar mejor resultado
        with open("resumenes/image_mejor_resultado.txt", 'w', encoding='utf-8') as f:
            f.write(best_text)
        
        print(f"\nMejor resultado: {len(best_text)} caracteres")
        
        return best_text
        
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return None

def extract_movements_from_image_text(text):
    """
    Extraer movimientos específicos del texto de la imagen
    """
    movements = []
    lines = text.split('\n')
    
    print(f"\nAnalizando {len(lines)} líneas de la imagen...")
    
    # Patrones para detectar movimientos en la imagen
    movement_patterns = [
        # Patrones para consumos con fechas y montos
        r'\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}.*[\d.,]+\s*$',  # Fecha + monto
        r'\d{1,2}\s+\w+\s+\d{2,4}.*[\d.,]+\s*$',  # 21 Enero 26 + monto
        r'.*\d{3,4}.*\d{1,5}[.,]\d{2}\s*$',  # Código + monto
        r'.*\$.*\d{1,5}[.,]\d{2}',  # $ + monto
        r'.*USD.*\d{1,5}[.,]\d{2}',  # USD + monto
        
        # Patrones específicos para tarjetas Macro
        r'\*\d{4,}.*\d{1,5}[.,]\d{2}',  # *1234 + monto
        r'MER.*\d{1,5}[.,]\d{2}',  # MERCADO PAGO + monto
        r'TC.*\d{1,5}[.,]\d{2}',  # TC + monto
    ]
    
    # Palabras a excluir
    exclude_words = [
        'RESUMEN', 'PÁGINA', 'TARJETA', 'CUENTA', 'SALDO', 'LÍMITE',
        'PAGO MÍNIMO', 'PAGO TOTAL', 'VENCIMIENTO', 'ESTADO DE CUENTA',
        'SUCURSAL', 'BANCO MACRO', 'IVA', 'TOTAL', 'SUBTOTAL'
    ]
    
    import re
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or len(line) < 8:
            continue
        
        # Convertir a mayúsculas para comparación
        line_upper = line.upper()
        
        # Excluir líneas con palabras no deseadas
        if any(word in line_upper for word in exclude_words):
            continue
        
        # Buscar patrones de movimiento
        is_movement = False
        for pattern in movement_patterns:
            if re.search(pattern, line):
                is_movement = True
                break
        
        # Adicional: buscar líneas con montos claros
        if not is_movement:
            # Buscar montos con formato argentino/europeo
            amount_match = re.search(r'\b\d{1,5}[.,]\d{2}\b', line)
            if amount_match and len(line) > 15:  # Línea suficientemente larga
                # Verificar que no sea solo un número
                non_digits = re.sub(r'[\d.,\s]', '', line)
                if len(non_digits) > 3:  # Tiene caracteres no numéricos
                    is_movement = True
        
        if is_movement:
            # Limpiar y estructurar el movimiento
            movement = {
                'linea': i+1,
                'texto_original': line,
                'texto_limpio': re.sub(r'\s+', ' ', line),
                'longitud': len(line)
            }
            
            # Intentar extraer monto
            amount_matches = re.findall(r'\b\d{1,5}[.,]\d{2}\b', line)
            if amount_matches:
                # El último monto encontrado suele ser el importe
                last_amount = amount_matches[-1].replace(',', '.')
                try:
                    movement['monto'] = float(last_amount)
                except ValueError:
                    movement['monto'] = None
            
            # Intentar extraer fecha
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,2})|(\d{1,2}\s+\w+\s+\d{2,4})', line)
            if date_match:
                movement['posible_fecha'] = date_match.group(0)
            
            movements.append(movement)
    
    return movements

def main():
    print("=== PROCESAR IMAGEN CONSUMOS BANCO MACRO ===")
    
    # Procesar imagen con OCR
    text = process_image_with_ocr()
    
    if text and len(text.strip()) > 50:
        print(f"\nOK - Imagen procesada: {len(text)} caracteres")
        
        # Mostrar primeras 20 líneas del texto extraído
        lines = text.split('\n')
        print("\nPrimeras 20 líneas del OCR:")
        for i, line in enumerate(lines[:20]):
            if line.strip():
                print(f"  {i+1:2}: {line}")
        
        # Extraer movimientos
        movements = extract_movements_from_image_text(text)
        
        if movements:
            print(f"\n=== MOVIMIENTOS ENCONTRADOS: {len(movements)} ===")
            
            # Agrupar por posibles categorías
            for i, movement in enumerate(movements[:30]):  # Mostrar primeros 30
                print(f"{i+1:2}: {movement['texto_original']}")
                if movement.get('monto'):
                    print(f"    Monto: ${movement['monto']:,.2f}")
                if movement.get('posible_fecha'):
                    print(f"    Fecha: {movement['posible_fecha']}")
                print()
            
            # Guardar movimientos
            output_json = f"image_movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"Todos los movimientos guardados en: {output_json}")
        else:
            print("\nNo se encontraron movimientos claros")
    else:
        print("\nError procesando la imagen")

if __name__ == "__main__":
    main()