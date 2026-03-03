#!/usr/bin/env python3
"""
Análisis completo del PDF para encontrar TODAS las tarjetas y movimientos
"""
import os
import json
from datetime import datetime

def analyze_pdf_structure():
    """
    Analizar la estructura completa del PDF
    """
    try:
        import pdfplumber
        import re
        
        pdf_path = "resumenes/descarga.pdf"
        
        print("=== ANÁLISIS ESTRUCTURA PDF COMPLETO ===")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF tiene {len(pdf.pages)} páginas")
            
            all_text = []
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n--- PÁGINA {page_num} ---")
                
                # Extraer texto
                text = page.extract_text()
                if text:
                    print(f"Texto: {len(text)} caracteres")
                    all_text.append(text)
                    
                    # Guardar texto de cada página
                    with open(f"resumenes/pagina_{page_num}_pdfplumber.txt", 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    # Buscar patrones de tarjetas
                    lines = text.split('\n')
                    potential_cards = []
                    
                    for line in lines:
                        line = line.strip()
                        if any(keyword in line.upper() for keyword in ['TARJETA', 'VISA', 'MASTERCARD', 'AMEX', 'NARANJA', 'CABAL']):
                            potential_cards.append(line)
                        elif re.search(r'\*\d{4,}', line):  # *1234
                            potential_cards.append(line)
                        elif re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', line):  # Números de tarjeta
                            potential_cards.append(line)
                    
                    if potential_cards:
                        print("Posibles tarjetas encontradas:")
                        for card in potential_cards:
                            print(f"  - {card}")
                
                # Extraer tablas
                tables = page.extract_tables()
                if tables:
                    print(f"Tablas encontradas: {len(tables)}")
                    all_tables.extend(tables)
                    
                    for i, table in enumerate(tables):
                        print(f"  Tabla {i+1}: {len(table)} filas x {len(table[0]) if table else 0} columnas")
                        
                        # Guardar tabla
                        table_file = f"resumenes/pagina_{page_num}_tabla_{i+1}.json"
                        with open(table_file, 'w', encoding='utf-8') as f:
                            json.dump(table, f, indent=2, ensure_ascii=False)
        
            # Combinar todo el texto
            combined_text = '\n\n'.join(all_text)
            with open("resumenes/pdf_completo_pdfplumber.txt", 'w', encoding='utf-8') as f:
                f.write(combined_text)
            
            print(f"\nTexto total extraído: {len(combined_text)} caracteres")
            
            # Buscar todos los posibles movimientos en el texto completo
            movements = find_all_movements_in_text(combined_text)
            
            return movements, all_tables
            
    except Exception as e:
        print(f"Error analizando PDF: {e}")
        return [], []

def find_all_movements_in_text(text):
    """
    Buscar todos los movimientos posibles en el texto
    """
    movements = []
    lines = text.split('\n')
    
    import re
    
    # Patrones más específicos para movimientos
    movement_patterns = [
        # Patrones de fecha + descripción + monto
        r'\d{1,2}[/-]\d{1,2}[/-]?\d{0,2}.+[\d.,]+\s*$',  # 21/01/26 ... 1234,56
        r'\d{1,2}\s+\w+\s+\d{2,4}.+[\d.,]+\s*$',  # 21 Enero 26 ... 1234,56
        
        # Patrones de consumo específicos
        r'.*COMPRA.*[\d.,]+\s*$',  # COMPRA ... 1234,56
        r'.*CONSUMO.*[\d.,]+\s*$',  # CONSUMO ... 1234,56
        r'.*PAGO.*[\d.,]+\s*$',  # PAGO ... 1234,56
        
        # Patrones con código de comercio + monto
        r'\d{5,}.+[\d.,]+\s*$',  # 123456 ... 1234,56
        
        # Patrones con $
        r'.*\$[\d.,]+',  # ...$1234,56
        
        # Patrones con USD
        r'.*USD[\d.,]+',  # ...USD1234,56
    ]
    
    # Palabras a excluir
    exclude_patterns = [
        r'RESUMEN', r'PÁGINA', r'TARJETA', r'CUENTA', r'SALDO',
        r'LÍMITE', r'PAGO\s+MÍNIMO', r'PAGO\s+TOTAL', r'VENCIMIENTO',
        r'IVA', r'TOTAL', r'SUBTOTAL', r'BANCO\s+MACRO'
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or len(line) < 10:
            continue
        
        # Excluir líneas no deseadas
        should_exclude = False
        for pattern in exclude_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # Buscar patrones de movimiento
        for pattern in movement_patterns:
            if re.search(pattern, line):
                # Intentar extraer datos estructurados
                movement = extract_structured_movement(line, i+1)
                movements.append(movement)
                break
    
    return movements

def extract_structured_movement(line, line_num):
    """
    Extraer datos estructurados de una línea de movimiento
    """
    import re
    
    movement = {
        'linea_numero': line_num,
        'texto_original': line,
        'texto_limpio': re.sub(r'\s+', ' ', line)
    }
    
    # Extraer fecha
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,2})',
        r'(\d{1,2}\s+\w+\s+\d{2,4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, line)
        if match:
            movement['fecha'] = match.group(1)
            break
    
    # Extraer monto
    amount_patterns = [
        r'\$?\s*([\d.,]+\s*$',  # $1234,56 al final
        r'\$?\s*([\d.,]+)',  # $1234,56 en cualquier lugar
        r'USD\s*([\d.,]+)',  # USD1234,56
        r'\b([\d.,]+\d{2})\s*$',  # 1234,56 al final (2 decimales)
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, line)
        if matches:
            # Tomar el último monto encontrado (suele ser el importe)
            amount_str = matches[-1].replace(',', '.')
            try:
                movement['monto'] = float(amount_str)
            except ValueError:
                pass
            break
    
    # Extraer código de comercio
    code_match = re.search(r'\b(\d{5,})\b', line)
    if code_match:
        movement['codigo_comercio'] = code_match.group(1)
    
    # Extractar descripción (remover fecha y monto)
    description = line
    if movement.get('fecha'):
        description = description.replace(movement['fecha'], '')
    if movement.get('monto'):
        description = re.sub(r'\$?\s*[\d.,]+\s*$', '', description)
    
    movement['descripcion'] = description.strip()
    
    return movement

def main():
    print("=== ANÁLISIS COMPLETO PDF BANCO MACRO ===")
    
    # Analizar estructura del PDF
    movements, tables = analyze_pdf_structure()
    
    if movements:
        print(f"\n=== TOTAL MOVIMIENTOS ENCONTRADOS: {len(movements)} ===")
        
        # Agrupar por tarjetas si es posible
        card_groups = {}
        
        for movement in movements:
            # Intentar identificar la tarjeta
            descripcion = movement.get('descripcion', '').upper()
            
            tarjeta = 'SIN TARJETA IDENTIFICADA'
            
            if 'VISA' in descripcion:
                tarjeta = 'VISA'
            elif 'MASTERCARD' in descripcion:
                tarjeta = 'MASTERCARD'
            elif 'AMEX' in descripcion:
                tarjeta = 'AMEX'
            elif 'NARANJA' in descripcion:
                tarjeta = 'NARANJA'
            elif 'CABAL' in descripcion:
                tarjeta = 'CABAL'
            elif movement.get('codigo_comercio'):
                tarjeta = f"COD_{movement['codigo_comercio'][:6]}"
            
            if tarjeta not in card_groups:
                card_groups[tarjeta] = []
            card_groups[tarjeta].append(movement)
        
        print(f"\nTarjetas identificadas: {len(card_groups)}")
        
        for tarjeta, movs in card_groups.items():
            total = sum(m.get('monto', 0) for m in movs if m.get('monto'))
            print(f"\n{tarjeta}: {len(movs)} movimientos - Total: ${total:,.2f}")
            
            # Mostrar primeros 3 movimientos de esta tarjeta
            for i, mov in enumerate(movs[:3]):
                print(f"  {i+1}. {mov.get('fecha', 'Sin fecha')} - ${mov.get('monto', 0):,.2f}")
                print(f"     {mov.get('descripcion', 'Sin descripción')[:60]}...")
        
        # Guardar todos los movimientos
        output_json = f"pdf_todos_movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(movements, f, indent=2, ensure_ascii=False)
        
        print(f"\nTodos los movimientos guardados en: {output_json}")
        
        # Guardar resumen por tarjeta
        summary_file = output_json.replace('.json', '_resumen.json')
        summary = {
            'total_movimientos': len(movements),
            'tarjetas': {}
        }
        
        for tarjeta, movs in card_groups.items():
            total = sum(m.get('monto', 0) for m in movs if m.get('monto'))
            summary['tarjetas'][tarjeta] = {
                'cantidad': len(movs),
                'total': total,
                'movimientos': movs
            }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Resumen por tarjeta guardado en: {summary_file}")
        
    else:
        print("\nNo se encontraron movimientos en el PDF")
        print("Revisa los archivos generados en resumenes/ para análisis manual")

if __name__ == "__main__":
    main()