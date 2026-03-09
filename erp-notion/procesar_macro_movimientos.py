#!/usr/bin/env python3
"""
Procesar y estructurar los movimientos extraídos de Banco Macro
"""
import json
import re
from datetime import datetime

def parse_movement_data(movement_text):
    """
    Parsea los datos de un movimiento extraído por OCR
    Formato típico: "21 Enero 26 299306 * MERPAGO*ALWAYSRENTACA C.61/86 8691,15"
    """
    # Patrones regex
    date_pattern = r'(\d{1,2})\s+(\w+)\s+(\d{2,4})'
    amount_pattern = r'([\d.,]+)$'  # Último número en la línea
    
    try:
        # Extraer fecha
        date_match = re.search(date_pattern, movement_text)
        if date_match:
            day = date_match.group(1).zfill(2)
            month = date_match.group(2)
            year = date_match.group(3)
            
            # Convertir mes a número
            month_map = {
                'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
                'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
                'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
            }
            
            month_num = month_map.get(month, month)
            formatted_date = f"{day}/{month_num}/{year}"
        else:
            formatted_date = None
        
        # Extraer monto
        amount_match = re.search(amount_pattern, movement_text)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '.')
            try:
                amount = float(amount_str)
            except ValueError:
                amount = None
        else:
            amount = None
        
        # Extraer descripción (todo excepto fecha y monto)
        if date_match and amount_match:
            # Remover fecha y monto para obtener descripción
            temp_text = movement_text.replace(date_match.group(0), '', 1)
            description = temp_text.replace(amount_match.group(0), '').strip()
            description = re.sub(r'\s+', ' ', description)  # Limpiar espacios
        else:
            description = movement_text
        
        return {
            'fecha': formatted_date,
            'monto': amount,
            'descripcion': description,
            'texto_original': movement_text,
            'moneda': 'ARS'  # Por defecto pesos argentinos
        }
        
    except Exception as e:
        return {
            'fecha': None,
            'monto': None,
            'descripcion': movement_text,
            'texto_original': movement_text,
            'error': str(e)
        }

def process_macro_movements():
    """
    Procesa los movimientos del archivo JSON generado por OCR
    """
    # Buscar el archivo más reciente de consumos OCR
    import glob
    
    pattern = "macro_consumos_ocr_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print("No se encontraron archivos de consumos OCR")
        return []
    
    latest_file = max(files)
    print(f"Procesando archivo: {latest_file}")
    
    # Cargar datos
    with open(latest_file, 'r', encoding='utf-8') as f:
        movements_data = json.load(f)
    
    processed_movements = []
    
    for movement in movements_data:
        text = movement['texto']
        parsed = parse_movement_data(text)
        parsed.update({
            'linea_numero': movement['linea']
        })
        processed_movements.append(parsed)
    
    return processed_movements

def categorize_movements(movements):
    """
    Categoriza los movimientos según su descripción
    """
    categories = {
        'ALQUILER': ['ALWAYSRENTACA', 'RENTA', 'ALQUILER'],
        'AEROLINEAS': ['AEROLINEAS', 'VUELO'],
        'LIMPIEZA': ['MASTER CLEAN', 'CLEAN', 'LIMPIEZA'],
        'SERVICIOS': ['VIUMI', 'RENTEC', 'SERVICIO'],
        'OTROS': []
    }
    
    for movement in movements:
        description = movement['descripcion'].upper()
        category = 'OTROS'
        
        for cat_name, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                category = cat_name
                break
        
        movement['categoria'] = category
    
    return movements

def main():
    print("=== PROCESAMIENTO MOVIMIENTOS BANCO MACRO ===")
    
    # Procesar movimientos
    movements = process_macro_movements()
    
    if not movements:
        print("No se encontraron movimientos para procesar")
        return
    
    # Categorizar
    movements = categorize_movements(movements)
    
    print(f"\nMovimientos procesados: {len(movements)}")
    
    # Resumen por categoría
    category_summary = {}
    total_amount = 0
    
    for movement in movements:
        cat = movement['categoria']
        amount = movement.get('monto', 0) or 0
        
        if cat not in category_summary:
            category_summary[cat] = {'count': 0, 'total': 0}
        
        category_summary[cat]['count'] += 1
        category_summary[cat]['total'] += amount
        total_amount += amount
    
    print("\n=== RESUMEN POR CATEGORÍA ===")
    for category, data in category_summary.items():
        print(f"{category}: {data['count']} movimientos - Total: ${data['total']:,.2f}")
    
    print(f"\nTOTAL GENERAL: ${total_amount:,.2f}")
    
    # Mostrar detalles
    print("\n=== DETALLE DE MOVIMIENTOS ===")
    for i, movement in enumerate(movements):
        print(f"\n{i+1}. {movement['fecha'] or 'Sin fecha'} - ${movement.get('monto', 0):,.2f}")
        print(f"   Categoría: {movement['categoria']}")
        print(f"   Descripción: {movement['descripcion']}")
    
    # Guardar procesados
    output_file = f"macro_consumos_procesados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movements, f, indent=2, ensure_ascii=False)
    
    print(f"\nMovimientos procesados guardados en: {output_file}")
    
    # Generar CSV para fácil visualización
    csv_file = output_file.replace('.json', '.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('Fecha,Monto,Descripcion,Categoria,Original\n')
        for movement in movements:
            f.write(f"{movement['fecha'] or ''},{movement.get('monto', '')},{movement['descripcion']},{movement['categoria']},{movement['texto_original']}\n")
    
    print(f"CSV generado en: {csv_file}")

if __name__ == "__main__":
    main()