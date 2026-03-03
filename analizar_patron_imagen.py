#!/usr/bin/env python3
"""
Procesar imagen específica para encontrar el patrón exacto de consumos
"""
import os
import json
import re
from datetime import datetime

def process_specific_image():
    """
    Procesar la imagen específica con OCR avanzado
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
        
        print("=== PROCESANDO IMAGEN ESPECÍFICA ===")
        print(f"Imagen: {image_path}")
        
        # Abrir imagen
        image = Image.open(image_path)
        print(f"Dimensiones: {image.size}")
        
        # Procesar con múltiples técnicas
        all_results = {}
        
        # 1. Imagen original
        print("\n1. Procesando imagen original...")
        all_results['original'] = process_with_configs(image, "original")
        
        # 2. Escala de grises
        print("\n2. Procesando escala de grises...")
        gray = image.convert('L')
        all_results['gris'] = process_with_configs(gray, "gris")
        
        # 3. Alto contraste
        print("\n3. Procesando alto contraste...")
        enhanced = ImageEnhance.Contrast(gray).enhance(3.0)
        all_results['contraste'] = process_with_configs(enhanced, "contraste")
        
        # 4. Binarización
        print("\n4. Procesando binarización...")
        threshold = 128
        binary = enhanced.point(lambda x: 0 if x < threshold else 255, '1')
        all_results['binario'] = process_with_configs(binary, "binario")
        
        # 5. Nitidez mejorada
        print("\n5. Procesando nitidez...")
        sharp = ImageEnhance.Sharpness(enhanced).enhance(2.0)
        all_results['nitido'] = process_with_configs(sharp, "nitido")
        
        # Analizar cuál es el mejor resultado
        best_result = None
        best_score = 0
        best_method = ""
        
        for method, text in all_results.items():
            score = evaluate_text_quality(text)
            print(f"{method}: {score} puntos - {len(text)} caracteres")
            
            if score > best_score:
                best_score = score
                best_result = text
                best_method = method
        
        print(f"\nMejor método: {best_method} ({best_score} puntos)")
        
        # Guardar mejor resultado
        with open("resumenes/mejor_resultado_imagen.txt", 'w', encoding='utf-8') as f:
            f.write(best_result)
        
        return best_result, all_results
        
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return None, {}

def process_with_configs(image, method_name):
    """
    Procesar imagen con múltiples configuraciones OCR
    """
    configs = [
        ('auto', '--oem 3 --psm 3 -l spa+eng'),
        ('bloque', '--oem 3 --psm 6 -l spa+eng'),
        ('columna', '--oem 3 --psm 4 -l spa+eng'),
        ('denso', '--oem 3 --psm 11 -l spa+eng'),
        ('linea', '--oem 3 --psm 13 -l spa+eng'),
        ('palabra', '--oem 3 --psm 8 -l spa+eng'),
    ]
    
    import pytesseract
    results = {}
    
    for config_name, config in configs:
        try:
            text = pytesseract.image_to_string(image, config=config)
            results[config_name] = text
        except Exception as e:
            print(f"  Error {config_name}: {e}")
            results[config_name] = ""
    
    # Devolver el mejor resultado de este método
    best_config = max(results.items(), key=lambda x: len(x[1]))
    print(f"  {method_name} - Mejor config: {best_config[0]} ({len(best_config[1])} chars)")
    
    return best_config[1]

def evaluate_text_quality(text):
    """
    Evaluar la calidad del texto extraído
    """
    if not text:
        return 0
    
    score = 0
    
    # Puntos por longitud
    score += len(text) / 10
    
    # Puntos por líneas
    lines = text.split('\n')
    score += len([l for l in lines if l.strip()]) * 5
    
    # Puntos por palabras en español comunes
    spanish_words = ['fecha', 'consumo', 'compra', 'pago', 'tarjeta', 'visa', 'mastercard', 'naranja', 'cabal']
    for word in spanish_words:
        score += text.lower().count(word) * 20
    
    # Puntos por patrones de fechas
    date_patterns = [r'\d{2}[/-]\d{2}[/-]?\d{0,2}', r'\d{1,2}\s+\w+\s+\d{2,4}']
    for pattern in date_patterns:
        score += len(re.findall(pattern, text)) * 10
    
    # Puntos por montos
    amount_pattern = r'\$?\s*\d{1,5}[.,]\d{2}'
    score += len(re.findall(amount_pattern, text)) * 15
    
    return score

def analyze_movement_patterns(text):
    """
    Analizar patrones específicos de movimientos
    """
    lines = text.split('\n')
    
    print("\n=== ANÁLISIS DE PATRONES DE MOVIMIENTOS ===")
    
    # Mostrar primeras 50 líneas para análisis manual
    print("Primeras 50 líneas del texto:")
    for i, line in enumerate(lines[:50]):
        if line.strip():
            print(f"{i+1:2}: {repr(line)}")
    
    # Buscar posibles patrones
    print("\nBúsqueda de patrones:")
    
    # 1. Líneas con fechas
    date_lines = []
    for i, line in enumerate(lines):
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}|d{1,2}\s+\w+\s+d{2,4}', line):
            date_lines.append((i+1, line.strip()))
    
    print(f"Líneas con fechas: {len(date_lines)}")
    for line_num, line in date_lines[:10]:
        print(f"  {line_num}: {line}")
    
    # 2. Líneas con montos
    amount_lines = []
    for i, line in enumerate(lines):
        if re.search(r'\$?\s*\d{1,5}[.,]\d{2}', line):
            amount_lines.append((i+1, line.strip()))
    
    print(f"Líneas con montos: {len(amount_lines)}")
    for line_num, line in amount_lines[:10]:
        print(f"  {line_num}: {line}")
    
    # 3. Líneas que podrían ser movimientos completos
    movement_candidates = []
    for i, line in enumerate(lines):
        line = line.strip()
        if (len(line) > 20 and 
            re.search(r'\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}|d{1,2}\s+\w+\s+d{2,4}', line) and
            re.search(r'\$?\s*\d{1,5}[.,]\d{2}', line)):
            movement_candidates.append((i+1, line))
    
    print(f"\nCandidatos a movimientos completos: {len(movement_candidates)}")
    for line_num, line in movement_candidates[:15]:
        print(f"  {line_num}: {line}")
    
    return movement_candidates

def main():
    print("=== ANÁLISIS DE IMAGEN ESPECÍFICA PARA PATRONES ===")
    
    # Procesar imagen
    best_text, all_results = process_specific_image()
    
    if best_text:
        # Analizar patrones
        movements = analyze_movement_patterns(best_text)
        
        # Guardar todos los resultados para análisis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Guardar todos los textos por método
        for method, text in all_results.items():
            filename = f"resumenes/imagen_{method}_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
        
        # Guardar candidatos a movimientos
        if movements:
            movements_file = f"resumenes/candidatos_movimientos_{timestamp}.json"
            with open(movements_file, 'w', encoding='utf-8') as f:
                json.dump([{'linea': ln, 'texto': t} for ln, t in movements], f, indent=2, ensure_ascii=False)
            
            print(f"\nCandidatos guardados: {movements_file}")
        
        print(f"\nTodos los resultados guardados en resumenes/")
        print("Revisa los archivos .txt para ver diferentes configuraciones OCR")
        
    else:
        print("No se pudo procesar la imagen")

if __name__ == "__main__":
    main()