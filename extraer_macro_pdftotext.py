#!/usr/bin/env python3
"""
Extractor de datos de PDF de Banco Macro usando pdftotext
"""
import subprocess
import os
import json
import re
from datetime import datetime

def extract_text_from_pdf(pdf_path, output_txt=None):
    """
    Extrae texto del PDF usando pdftotext
    
    Args:
        pdf_path: Ruta al archivo PDF
        output_txt: Ruta al archivo de texto de salida (opcional)
    
    Returns:
        str: Texto extraído del PDF
    """
    if output_txt is None:
        output_txt = pdf_path.replace('.pdf', '_extraido.txt')
    
    # Usar pdftotext con opciones optimizadas para tablas
    cmd = [
        'pdftotext',
        '-layout',  # Mantener layout original
        '-table',   # Optimizado para tablas
        '-enc', 'UTF-8',  # Codificación UTF-8
        pdf_path,
        output_txt
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Texto extraído y guardado en: {output_txt}")
        
        # Leer el archivo de texto generado
        with open(output_txt, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return text
    except subprocess.CalledProcessError as e:
        print(f"Error al extraer texto: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def parse_macro_extracted_data(text):
    """
    Parsea el texto extraído del PDF de Banco Macro
    """
    movements = []
    lines = text.split('\n')
    
    # Patrones para identificar movimientos
    # Ajustar estos patrones según el formato exacto del PDF de Macro
    date_pattern = r'(\d{2}/\d{2}/\d{2})'
    amount_pattern = r'([\d.,]+)'
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('PÁGINA') or line.startswith('RESUMEN'):
            continue
            
        # Buscar líneas que parezcan movimientos
        # Esto necesitará ajuste según el formato real
        if re.search(date_pattern, line) and ('$' in line or 'USD' in line):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    # Intentar extraer fecha, descripción y monto
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        date = date_match.group(1)
                        # El resto de la lógica dependerá del formato específico
                        description = " ".join(parts[1:-1])
                        amount = parts[-1]
                        
                        movement = {
                            'fecha': date,
                            'descripcion': description,
                            'monto': amount,
                            'linea_original': line
                        }
                        movements.append(movement)
                except Exception as e:
                    print(f"Error parseando línea {i}: {line}")
                    print(f"Error: {e}")
    
    return movements

def main():
    # Ruta al PDF del resumen de Banco Macro
    pdf_path = "resumenes/descarga.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"No se encuentra el archivo: {pdf_path}")
        return
    
    print("Extrayendo texto del PDF...")
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if extracted_text:
        print("Texto extraído exitosamente.")
        print("\n=== PRIMERAS 20 LÍNEAS DEL TEXTO EXTRAÍDO ===")
        lines = extracted_text.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2}: {line}")
        
        print("\n=== ANALIZANDO ESTRUCTURA PARA MOVIMIENTOS ===")
        movements = parse_macro_extracted_data(extracted_text)
        
        if movements:
            print(f"\nSe encontraron {len(movements)} movimientos:")
            for i, movement in enumerate(movements[:10]):  # Mostrar primeros 10
                print(f"{i+1}: {movement}")
            
            # Guardar movimientos en JSON
            output_json = "macro_consumos_pdftotext.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"\nMovimientos guardados en: {output_json}")
        else:
            print("No se encontraron movimientos. Es posible que necesitemos ajustar los patrones de parsing.")
            
            # Guardar texto completo para análisis manual
            with open("macro_texto_completo.txt", 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print("Texto completo guardado en: macro_texto_completo.txt")
    else:
        print("Error al extraer texto del PDF")

if __name__ == "__main__":
    main()