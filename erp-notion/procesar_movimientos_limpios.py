#!/usr/bin/env python3
"""
Procesar y limpiar los movimientos extraídos del PDF de Banco Macro
"""
import json
import re
from datetime import datetime

def clean_and_structure_movements():
    """
    Limpiar y estructurar los movimientos extraídos
    """
    # Buscar el archivo más reciente
    import glob
    files = glob.glob("macro_movimientos_rapidos_*.json")
    if not files:
        print("No se encontraron archivos de movimientos")
        return []
    
    latest_file = max(files)
    print(f"Procesando archivo: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        movements = json.load(f)
    
    cleaned_movements = []
    
    for movement in movements:
        original = movement['texto_original']
        
        # Extraer fecha correctamente
        fecha = None
        
        # Buscar patrones de fecha
        date_patterns = [
            r'(\d{1,2}\s+\w+\s+\d{2,4})',  # 21 Enero 26
            r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,2})',  # 21/01/26
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, original)
            if match:
                fecha = match.group(1)
                break
        
        # Extraer monto (el último número con 2 decimales)
        monto = None
        amount_matches = re.findall(r'\b(\d{1,5}[.,]\d{2})\b', original)
        if amount_matches:
            try:
                # El último monto suele ser el del movimiento
                monto_str = amount_matches[-1].replace(',', '.')
                monto = float(monto_str)
            except ValueError:
                pass
        
        # Extraer descripción limpia
        descripcion = original
        
        # Remover fecha
        if fecha:
            descripcion = descripcion.replace(fecha, '')
        
        # Remover montos
        descripcion = re.sub(r'\$?\s*[\d.,]+\s*$', '', descripcion)  # Monto al final
        descripcion = re.sub(r'\b\d{5,}[.,]\d{2}\b', '', descripcion)  # Montos grandes
        
        # Remover códigos de comercio
        descripcion = re.sub(r'\b\d{5,}\b', '', descripcion)
        
        # Limpiar espacios y caracteres especiales
        descripcion = re.sub(r'[^\w\s\*\-\./]', ' ', descripcion)
        descripcion = re.sub(r'\s+', ' ', descripcion).strip()
        
        # Filtrar descripciones muy cortas o sin sentido
        if len(descripcion) < 5:
            descripcion = original  # Usar original si la limpieza la daña
        
        # Categorizar el movimiento
        categoria = categorizar_movimiento(descripcion, monto)
        
        cleaned_movement = {
            'fecha': fecha,
            'monto': monto,
            'descripcion': descripcion,
            'categoria': categoria,
            'texto_original': original,
            'pagina': movement['pagina'],
            'linea': movement['linea']
        }
        
        # Solo incluir si tiene datos válidos
        if monto is not None and monto > 0:
            cleaned_movements.append(cleaned_movement)
    
    return cleaned_movements

def categorizar_movimiento(descripcion, monto):
    """
    Categorizar movimiento basado en descripción y monto
    """
    desc_upper = descripcion.upper()
    
    # Categorías específicas
    categorias = {
        'ALQUILER': ['ALWAYS', 'RENTA', 'ALQUILER', 'INMUEBLE'],
        'TRANSPORTE': ['AEROLINEAS', 'AERO', 'PASAJES', 'TAXI', 'UBER', 'REMIS'],
        'MERCADO': ['MERCADO', 'SUPER', 'CARREFOUR', 'COTO', 'DISCO', 'WALMART'],
        'COMPRA': ['COMPRA', 'SHOPPING', 'ROPA', 'ZAPATOS', 'TIENDA'],
        'SERVICIO': ['LUZ', 'AGUA', 'GAS', 'INTERNET', 'TELEFONO', 'NETFLIX'],
        'RESTAURANTE': ['RESTAURAN', 'COMIDA', 'CAFE', 'PIZZA', 'HAMBURGUESA'],
        'COMBUSTIBLE': ['YPF', 'SHELL', 'AXION', 'GASOLINA', 'NAFTA', 'COMBUSTIBLE'],
        'FARMACIA': ['FARMACIA', 'DROGUERIA', 'MEDICAMENTO'],
        'PINTURERIA': ['PINTURERIA', 'PINTURA', 'HERRAMIENTA'],
        'TRANSFERENCIA': ['TRANSFERENCIA', 'DEBITO', 'CREDITO'],
        'LIMITE/TC': ['LIMITE', 'TARJETA', 'TC', 'FINANCIACION'],
    }
    
    # Buscar categoría
    for categoria, keywords in categorias.items():
        if any(keyword in desc_upper for keyword in keywords):
            return categoria
    
    # Categorías basadas en monto
    if monto > 50000:
        return 'GASTO GRANDE'
    elif monto > 10000:
        return 'GASTO MEDIANO'
    elif monto > 1000:
        return 'GASTO CHICO'
    else:
        return 'OTRO'

def generar_reporte(movements):
    """
    Generar reporte completo de los movimientos
    """
    # Agrupar por categoría
    categorias = {}
    total_general = 0
    
    for movement in movements:
        cat = movement['categoria']
        monto = movement['monto']
        
        if cat not in categorias:
            categorias[cat] = {'count': 0, 'total': 0, 'movimientos': []}
        
        categorias[cat]['count'] += 1
        categorias[cat]['total'] += monto
        categorias[cat]['movimientos'].append(movement)
        total_general += monto
    
    print("\n" + "="*60)
    print("REPORTE COMPLETO DE MOVIMIENTOS BANCO MACRO")
    print("="*60)
    
    print(f"\nTotal de movimientos: {len(movements)}")
    print(f"Total general: ${total_general:,.2f}")
    
    print(f"\nResumen por categoría:")
    for categoria, data in sorted(categorias.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"  {categoria}: {data['count']} movimientos - ${data['total']:,.2f}")
    
    print(f"\nDetalle por categoría:")
    for categoria, data in sorted(categorias.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"\n{categoria} (${data['total']:,.2f}):")
        
        # Ordenar por monto descendente
        movs_ordenados = sorted(data['movimientos'], key=lambda x: x['monto'], reverse=True)
        
        for i, mov in enumerate(movs_ordenados[:5]):  # Top 5 por categoría
            print(f"  {i+1}. {mov.get('fecha', 'Sin fecha')} - ${mov['monto']:>10,.2f} - {mov['descripcion'][:50]}")
        
        if len(movs_ordenados) > 5:
            print(f"  ... y {len(movs_ordenados) - 5} movimientos más")
    
    return categorias

def main():
    print("=== PROCESAMIENTO Y LIMPIEZA DE MOVIMIENTOS ===")
    
    # Limpiar y estructurar
    movements = clean_and_structure_movements()
    
    if movements:
        # Generar reporte
        categorias = generar_reporte(movements)
        
        # Guardar resultados limpios
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON limpio
        clean_file = f"macro_movimientos_limpios_{timestamp}.json"
        with open(clean_file, 'w', encoding='utf-8') as f:
            json.dump(movements, f, indent=2, ensure_ascii=False)
        
        print(f"\nMovimientos limpios guardados: {clean_file}")
        
        # CSV limpio
        csv_file = clean_file.replace('.json', '.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('Fecha,Monto,Categoria,Descripcion,Original\n')
            for mov in movements:
                f.write(f"{mov.get('fecha', '')},{mov.get('monto', '')},{mov.get('categoria', '')},\"{mov.get('descripcion', '')}\",\"{mov.get('texto_original', '')}\"\n")
        
        print(f"CSV limpio generado: {csv_file}")
        
        # Resumen por categoría JSON
        summary_file = f"macro_resumen_categoria_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(categorias, f, indent=2, ensure_ascii=False)
        
        print(f"Resumen por categoría guardado: {summary_file}")
        
    else:
        print("No se encontraron movimientos válidos para procesar")

if __name__ == "__main__":
    main()