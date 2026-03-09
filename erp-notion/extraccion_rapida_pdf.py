#!/usr/bin/env python3
"""
Extracción rápida de movimientos del PDF de Banco Macro
"""
import os
import json
from datetime import datetime

def quick_pdf_extraction():
    """
    Extracción rápida pero efectiva
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
        
        print("=== EXTRACCIÓN RÁPIDA PDF MACRO ===")
        
        # Convertir con DPI moderado para velocidad
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        
        all_movements = []
        
        for page_num, image in enumerate(images, 1):
            print(f"\nProcesando página {page_num}...")
            
            # Mejora rápida
            gray = image.convert('L')
            enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
            
            # OCR con la mejor configuración
            config = '--oem 3 --psm 6 -l spa+eng'
            text = pytesseract.image_to_string(enhanced, config=config)
            
            print(f"Texto extraído: {len(text)} caracteres")
            
            # Extraer movimientos
            movements = extract_movements_quick(text, page_num)
            
            if movements:
                print(f"Movimientos encontrados: {len(movements)}")
                all_movements.extend(movements)
                
                # Mostrar primeros 3
                for i, mov in enumerate(movements[:3]):
                    print(f"  {i+1}. ${mov.get('monto', 0):,.2f} - {mov.get('descripcion', '')[:40]}")
            else:
                print("No se encontraron movimientos en esta página")
        
        return all_movements
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def extract_movements_quick(text, page_num):
    """
    Extracción rápida de movimientos
    """
    movements = []
    lines = text.split('\n')
    
    import re
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or len(line) < 15:
            continue
        
        # Excluir líneas que no son movimientos
        exclude_terms = [
            'RESUMEN', 'PÁGINA', 'TARJETA', 'CUENTA', 'SALDO', 'LÍMITE',
            'PAGO MÍNIMO', 'PAGO TOTAL', 'VENCIMIENTO', 'ESTADO DE CUENTA',
            'BANCO MACRO', 'IVA', 'IMPUESTO', 'TOTAL', 'SUBTOTAL'
        ]
        
        if any(term in line.upper() for term in exclude_terms):
            continue
        
        # Buscar líneas con montos (formato argentino)
        amount_match = re.search(r'\b(\d{1,5}[.,]\d{2})\b', line)
        if not amount_match:
            continue
        
        # Si tiene monto y es suficientemente larga, probablemente es un movimiento
        if len(line) > 20:
            movement = {
                'pagina': page_num,
                'linea': i+1,
                'texto_original': line
            }
            
            # Extraer monto
            try:
                amount_str = amount_match.group(1).replace(',', '.')
                movement['monto'] = float(amount_str)
            except ValueError:
                continue
            
            # Buscar fecha
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,2})|(\d{1,2}\s+\w+\s+\d{2,4})', line)
            if date_match:
                movement['fecha'] = date_match.group(0)
            
            # Descripción (todo excepto fecha y monto)
            descripcion = line
            if movement.get('fecha'):
                descripcion = descripcion.replace(movement['fecha'], '')
            if movement.get('monto'):
                descripcion = re.sub(r'\b\d{1,5}[.,]\d{2}\s*$', '', descripcion)
            
            movement['descripcion'] = descripcion.strip()
            
            movements.append(movement)
    
    return movements

def main():
    print("=== EXTRACCIÓN RÁPIDA MOVIMIENTOS BANCO MACRO ===")
    
    movements = quick_pdf_extraction()
    
    if movements:
        print(f"\n=== TOTAL MOVIMIENTOS: {len(movements)} ===")
        
        # Agrupar por páginas
        pages = {}
        total = 0
        
        for mov in movements:
            page = mov['pagina']
            if page not in pages:
                pages[page] = []
            pages[page].append(mov)
            if mov.get('monto'):
                total += mov['monto']
        
        print("\nResumen por página:")
        for page, movs in sorted(pages.items()):
            page_total = sum(m.get('monto', 0) for m in movs)
            print(f"  Página {page}: {len(movs)} movimientos - ${page_total:,.2f}")
        
        print(f"\nTOTAL GENERAL: ${total:,.2f}")
        
        # Guardar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON completo
        json_file = f"macro_movimientos_rapidos_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(movements, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Movimientos guardados: {json_file}")
        
        # CSV para Excel
        csv_file = json_file.replace('.json', '.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('Página,Fecha,Monto,Descripción,Original\n')
            for mov in movements:
                f.write(f"{mov.get('pagina', '')},{mov.get('fecha', '')},{mov.get('monto', '')},\"{mov.get('descripcion', '')}\",\"{mov.get('texto_original', '')}\"\n")
        
        print(f"✓ CSV generado: {csv_file}")
        
        # Mostrar todos los movimientos
        print(f"\n=== DETALLE COMPLETO ===")
        for i, mov in enumerate(movements):
            print(f"{i+1:2}. P{mov.get('pagina', '?')} | {mov.get('fecha', 'Sin fecha')} | ${mov.get('monto', 0):>10,.2f} | {mov.get('descripcion', 'Sin descripción')[:50]}")
        
    else:
        print("\n❌ No se encontraron movimientos")
        print("\nSugerencias:")
        print("1. Abre el PDF manualmente para verificar que tiene contenido")
        print("2. Intenta exportar el PDF como imagen desde el visor de PDF")
        print("3. Verifica que sea el archivo correcto")

if __name__ == "__main__":
    main()