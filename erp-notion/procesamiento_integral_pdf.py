#!/usr/bin/env python3
"""
Procesamiento combinado del PDF: OCR + Análisis manual + Múltiples técnicas
"""
import os
import json
from datetime import datetime

def comprehensive_pdf_processing():
    """
    Procesamiento completo con múltiples técnicas
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image, ImageEnhance
        
        # Configurar rutas
        poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        pdf_path = "resumenes/descarga.pdf"
        
        print("=== PROCESAMIENTO INTEGRAL PDF ===")
        print("Convertir a imágenes de altísima calidad...")
        
        # Convertir con DPI muy alto
        images = convert_from_path(pdf_path, dpi=600, poppler_path=poppler_path)
        
        all_movements = []
        
        for page_num, image in enumerate(images, 1):
            print(f"\n=== PÁGINA {page_num} ===")
            
            # Guardar imagen original de alta calidad
            original_path = f"resumenes/pagina_{page_num}_hd.png"
            image.save(original_path, quality=100)
            
            # Aplicar múltiples mejoras
            processed_images = {}
            
            # 1. Imagen original
            processed_images['original'] = image
            
            # 2. Escala de grises con contraste alto
            gray = image.convert('L')
            enhanced = ImageEnhance.Contrast(gray).enhance(3.0)
            processed_images['contraste'] = enhanced
            
            # 3. Binarización
            threshold = 120
            binary = enhanced.point(lambda x: 0 if x < threshold else 255, '1')
            processed_images['binario'] = binary
            
            # 4. Nitidez mejorada
            sharp = ImageEnhance.Sharpness(enhanced).enhance(3.0)
            processed_images['nitidez'] = sharp
            
            # Procesar cada variación con múltiples configuraciones OCR
            ocr_configs = [
                ('auto', '--oem 3 --psm 3 -l spa+eng'),
                ('bloque', '--oem 3 --psm 6 -l spa+eng'),
                ('columna', '--oem 3 --psm 4 -l spa+eng'),
                ('denso', '--oem 3 --psm 11 -l spa+eng'),
                ('texto_solo', '--oem 3 --psm 7 -l spa+eng'),
                ('linea', '--oem 3 --psm 13 -l spa+eng'),
            ]
            
            best_text = ""
            best_length = 0
            best_method = ""
            
            for img_name, img_data in processed_images.items():
                print(f"\n  Procesando imagen {img_name}...")
                
                for config_name, config in ocr_configs:
                    try:
                        text = pytesseract.image_to_string(img_data, config=config)
                        
                        if len(text) > best_length:
                            best_length = len(text)
                            best_text = text
                            best_method = f"{img_name}_{config_name}"
                        
                        print(f"    {config_name}: {len(text)} chars")
                        
                    except Exception as e:
                        print(f"    {config_name}: Error - {e}")
            
            # Guardar mejor resultado de esta página
            page_file = f"resumenes/pagina_{page_num}_mejor.txt"
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(best_text)
            
            print(f"\n  Mejor método: {best_method} ({best_length} caracteres)")
            
            # Extraer movimientos del mejor texto
            movements = extract_movements_from_best_text(best_text, page_num)
            all_movements.extend(movements)
        
        return all_movements
        
    except Exception as e:
        print(f"Error en procesamiento integral: {e}")
        return []

def extract_movements_from_best_text(text, page_num):
    """
    Extraer movimientos del texto usando técnicas avanzadas
    """
    movements = []
    lines = text.split('\n')
    
    import re
    
    # Patrones muy específicos para consumos de tarjetas
    advanced_patterns = [
        # Formato completo: Fecha + Descripción + Monto
        r'^\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}\s+.+\s+[\d.,]+\s*$',  # 21/01/26 Descripción 1234,56
        r'^\d{1,2}\s+\w+\s+\d{2,4}\s+.+\s+[\d.,]+\s*$',  # 21 Enero 26 Descripción 1234,56
        
        # Formato con código de comercio
        r'^\d{5,}\s+.+\s+[\d.,]+\s*$',  # 123456 Descripción 1234,56
        
        # Formato con tarjeta
        r'^\*\d{4,}\s+.+\s+[\d.,]+\s*$',  # *1234 Descripción 1234,56
        
        # Formato solo con monto y descripción
        r'^.+\s+[\d.,]+\s*$',  # Descripción 1234,56 (mínimo 15 caracteres)
    ]
    
    # Palabras clave que indican movimientos
    movement_keywords = [
        'COMPRA', 'CONSUMO', 'PAGO', 'DEBITO', 'CREDITO', 'MERPAGO',
        'MERCADO', 'SUPERMERCADO', 'RESTAURANT', 'HOTEL', 'AEROLINEAS',
        'COMBUSTIBLE', 'ESTACION', 'FARMACIA', 'LIBRERIA', 'ROPA'
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or len(line) < 12:
            continue
        
        # Excluir líneas claramente no movimientos
        exclude_terms = [
            'RESUMEN', 'PÁGINA', 'TARJETA', 'CUENTA', 'SALDO', 'LÍMITE',
            'PAGO MÍNIMO', 'PAGO TOTAL', 'VENCIMIENTO', 'ESTADO DE CUENTA',
            'BANCO MACRO', 'SUCURSAL', 'IVA', 'IMPUESTO', 'TOTAL GENERAL'
        ]
        
        exclude = any(term in line.upper() for term in exclude_terms)
        if exclude:
            continue
        
        # Verificar si coincide con patrones de movimiento
        is_movement = False
        matched_pattern = None
        
        for pattern in advanced_patterns:
            if re.search(pattern, line):
                is_movement = True
                matched_pattern = pattern
                break
        
        # Si no coincide con patrones, buscar palabras clave + montos
        if not is_movement:
            has_keyword = any(keyword in line.upper() for keyword in movement_keywords)
            has_amount = bool(re.search(r'\b\d{1,5}[.,]\d{2}\b', line))
            
            if has_keyword and has_amount and len(line) > 20:
                is_movement = True
                matched_pattern = 'keyword_amount'
        
        if is_movement:
            # Estructurar el movimiento
            movement = {
                'pagina': page_num,
                'linea': i+1,
                'texto_original': line,
                'patron': str(matched_pattern)
            }
            
            # Extraer fecha
            date_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}|\d{1,2}\s+\w+\s+\d{2,4}', line)
            if date_matches:
                movement['fecha'] = date_matches[0]
            
            # Extraer monto (último número con formato de dinero)
            amount_matches = re.findall(r'\b\d{1,5}[.,]\d{2}\b', line)
            if amount_matches:
                try:
                    amount_str = amount_matches[-1].replace(',', '.')
                    movement['monto'] = float(amount_str)
                except ValueError:
                    pass
            
            # Extraer código de comercio
            code_match = re.search(r'\b(\d{5,})\b', line)
            if code_match:
                movement['codigo_comercio'] = code_match.group(1)
            
            # Descripción limpia
            descripcion = line
            if movement.get('fecha'):
                descripcion = descripcion.replace(movement['fecha'], '')
            if movement.get('codigo_comercio'):
                descripcion = descripcion.replace(movement['codigo_comercio'], '')
            if movement.get('monto'):
                descripcion = re.sub(r'\b\d{1,5}[.,]\d{2}\s*$', '', descripcion)
            
            movement['descripcion'] = descripcion.strip()
            
            movements.append(movement)
    
    return movements

def main():
    print("=== PROCESAMIENTO COMPLETO MULTI-TÉCNICA PDF MACRO ===")
    
    # Procesamiento integral
    movements = comprehensive_pdf_processing()
    
    if movements:
        print(f"\n=== TOTAL MOVIMIENTOS ENCONTRADOS: {len(movements)} ===")
        
        # Agrupar por página
        page_groups = {}
        for movement in movements:
            page = movement['pagina']
            if page not in page_groups:
                page_groups[page] = []
            page_groups[page].append(movement)
        
        print(f"\nMovimientos por página:")
        total_general = 0
        
        for page, movs in sorted(page_groups.items()):
            page_total = sum(m.get('monto', 0) for m in movs if m.get('monto'))
            print(f"\nPágina {page}: {len(movs)} movimientos - Total: ${page_total:,.2f}")
            
            for i, mov in enumerate(movs[:5]):  # Mostrar primeros 5 por página
                print(f"  {i+1}. {mov.get('fecha', 'Sin fecha')} - ${mov.get('monto', 0):,.2f}")
                print(f"     {mov.get('descripcion', 'Sin descripción')[:50]}...")
            
            if len(movs) > 5:
                print(f"     ... y {len(movs) - 5} movimientos más")
            
            total_general += page_total
        
        print(f"\n=== TOTAL GENERAL DE TODAS LAS TARJETAS: ${total_general:,.2f} ===")
        
        # Guardar todo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Movimientos completos
        movements_file = f"macro_completo_{timestamp}.json"
        with open(movements_file, 'w', encoding='utf-8') as f:
            json.dump(movements, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Movimientos guardados: {movements_file}")
        
        # Resumen por página
        summary_file = f"macro_resumen_{timestamp}.json"
        summary = {
            'total_movimientos': len(movements),
            'total_general': total_general,
            'paginas': {}
        }
        
        for page, movs in page_groups.items():
            page_total = sum(m.get('monto', 0) for m in movs if m.get('monto'))
            summary['paginas'][page] = {
                'cantidad': len(movs),
                'total': page_total,
                'movimientos': movs
            }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Resumen guardado: {summary_file}")
        
        # Generar CSV para Excel
        csv_file = f"macro_completo_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('Página,Fecha,Monto,Descripción,Código Comercio,Original\n')
            for mov in movements:
                f.write(f"{mov.get('pagina', '')},{mov.get('fecha', '')},{mov.get('monto', '')},{mov.get('descripcion', '')},{mov.get('codigo_comercio', '')},\"{mov.get('texto_original', '')}\"\n")
        
        print(f"✓ CSV generado: {csv_file}")
        
        return movements
        
    else:
        print("\n❌ No se encontraron movimientos con el procesamiento actual")
        print("\nRecomendaciones:")
        print("1. Revisa las imágenes HD generadas en resumenes/")
        print("2. Abre manualmente el PDF para verificar contenido")
        print("3. Considera exportar el PDF como imagen directamente")
        return []

if __name__ == "__main__":
    main()