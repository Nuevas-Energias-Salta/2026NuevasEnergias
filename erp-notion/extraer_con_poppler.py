#!/usr/bin/env python3
"""
Extraer PDF de Banco Macro con Poppler configurado
"""
import os
import subprocess
import json
from datetime import datetime

def main():
    print("=== EXTRACCIÓN PDF BANCO MACRO ===")
    
    # Configurar Poppler
    poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
    pdf_path = "resumenes/descarga.pdf"
    
    print(f"Usando Poppler: {poppler_path}")
    print(f"PDF a procesar: {pdf_path}")
    
    # Configurar environment
    env = os.environ.copy()
    env['PATH'] = poppler_path + os.pathsep + env.get('PATH', '')
    
    # Métodos de extracción
    methods = [
        ("layout", ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, "resumenes/layout.txt"]),
        ("table", ["pdftotext", "-table", "-enc", "UTF-8", pdf_path, "resumenes/table.txt"]),
        ("simple", ["pdftotext", "-simple", "-enc", "UTF-8", pdf_path, "resumenes/simple.txt"]),
        ("raw", ["pdftotext", "-raw", "-enc", "UTF-8", pdf_path, "resumenes/raw.txt"])
    ]
    
    best_result = None
    best_lines = 0
    
    for method_name, cmd in methods:
        print(f"\n--- Probando método: {method_name} ---")
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            output_file = cmd[-1]
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = [line for line in content.split('\n') if line.strip()]
                print(f"OK - {len(lines)} líneas extraídas")
                
                if lines:
                    print("Primeras 3 líneas:")
                    for i, line in enumerate(lines[:3]):
                        print(f"  {i+1}: {repr(line)}")
                
                # Guardar el mejor resultado
                if len(lines) > best_lines:
                    best_lines = len(lines)
                    best_result = {
                        'content': content,
                        'lines': lines,
                        'method': method_name,
                        'file': output_file
                    }
            
        except subprocess.CalledProcessError as e:
            print(f"X - Error: {e.stderr}")
    
    # Analizar mejor resultado
    if best_result and best_lines > 5:
        print(f"\n=== MEJOR RESULTADO: {best_result['method']} ===")
        print(f"Líneas: {best_lines}")
        
        # Guardar el mejor resultado
        final_file = "resumenes/macro_mejor_extraccion.txt"
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(best_result['content'])
        
        print(f"Guardado en: {final_file}")
        
        # Buscar movimientos
        movements = []
        for i, line in enumerate(best_result['lines']):
            # Líneas que podrían ser movimientos
            if any(keyword in line.upper() for keyword in ['$', 'USD', 'PESOS', 'CONSUMO', 'PAGO']) and any(char.isdigit() for char in line):
                movements.append({
                    'linea': i+1,
                    'texto': line.strip(),
                    'metodo': best_result['method']
                })
        
        if movements:
            print(f"\nMovimientos potenciales: {len(movements)}")
            for i, mov in enumerate(movements[:10]):
                print(f"  {i+1}: {mov['texto']}")
            
            # Guardar movimientos
            output_json = f"macro_consumos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"\nMovimientos guardados en: {output_json}")
            return True
        else:
            print("\nNo se encontraron movimientos claros")
    else:
        print("\nNo se pudo extraer contenido significativo")
        print("El PDF podría ser una imagen y requerir OCR")
    
    return False

if __name__ == "__main__":
    main()