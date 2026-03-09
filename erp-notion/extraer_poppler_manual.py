#!/usr/bin/env python3
"""
Extracción directa especificando ruta de Poppler
"""
import os
import subprocess
import json
from datetime import datetime

def extract_with_manual_poppler():
    """
    Intenta extracción con rutas comunes de Poppler
    """
    # Posibles rutas donde pudiste haber instalado Poppler
    poppler_paths = [
        r"C:\Program Files\poppler-24.02.0\Library\bin",
        r"C:\Program Files\poppler\bin", 
        r"C:\Users\Gonza\Downloads\poppler-24.02.0\Library\bin",
        r"C:\Users\Gonza\Desktop\poppler-24.02.0\Library\bin",
        r"D:\poppler-24.02.0\Library\bin",
    ]
    
    pdf_path = "resumenes/descarga.pdf"
    
    for poppler_path in poppler_paths:
        if os.path.exists(poppler_path):
            print(f"Intentando con Poppler en: {poppler_path}")
            
            # Extraer usando diferentes métodos
            methods = [
                ("layout", ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, "resumenes/salida_layout.txt"]),
                ("table", ["pdftotext", "-table", "-enc", "UTF-8", pdf_path, "resumenes/salida_table.txt"]),
                ("simple", ["pdftotext", "-simple", "-enc", "UTF-8", pdf_path, "resumenes/salida_simple.txt"])
            ]
            
            for method_name, cmd in methods:
                try:
                    # Set PATH temporalmente
                    env = os.environ.copy()
                    env['PATH'] = poppler_path + os.pathsep + env.get('PATH', '')
                    
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
                    
                    if result.returncode == 0:
                        output_file = cmd[-1]
                        if os.path.exists(output_file):
                            with open(output_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            lines = [line for line in content.split('\n') if line.strip()]
                            if len(lines) > 5:  # Si tiene contenido significativo
                                print(f"\nÉXITO con método {method_name}!")
                                print(f"Ruta Poppler: {poppler_path}")
                                print(f"Archivo: {output_file}")
                                print(f"Líneas extraídas: {len(lines)}")
                                
                                # Mostrar primeras líneas
                                print("\nPrimeras 5 líneas:")
                                for i, line in enumerate(lines[:5]):
                                    print(f"{i+1}: {repr(line)}")
                                
                                return content, poppler_path
                    
                except Exception as e:
                    print(f"Error con {method_name}: {e}")
        
        else:
            print(f"Ruta no existe: {poppler_path}")
    
    return None, None

def main():
    print("=== EXTRACCIÓN PDF BANCO MACRO ===")
    
    content, poppler_path = extract_with_manual_poppler()
    
    if content and len(content.strip()) > 100:
        print(f"\n✓ EXTRACCIÓN EXITOSA!")
        print(f"✓ Usando Poppler desde: {poppler_path}")
        
        # Guardar el mejor resultado
        with open("resumenes/macro_extraccion_final.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✓ Guardado en: resumenes/macro_extraccion_final.txt")
        
        # Extraer movimientos básicos
        lines = [line for line in content.split('\n') if line.strip()]
        movements = []
        
        for i, line in enumerate(lines):
            if any(char.isdigit() for char in line) and ('$' in line or 'USD' in line or 'PESOS' in line):
                movements.append({
                    'linea': i+1,
                    'texto': line
                })
        
        if movements:
            print(f"\nMovimientos potenciales encontrados: {len(movements)}")
            for mov in movements[:10]:
                print(f"  {mov['linea']}: {mov['texto']}")
            
            # Guardar movimientos
            output_json = f"macro_consumos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(movements, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Movimientos guardados en: {output_json}")
        
    else:
        print("\n✗ No se pudo extraer contenido del PDF")
        print("\nRecomendaciones:")
        print("1. Verifica la ruta de Poppler")
        print("2. El PDF podría estar protegido o ser imagen")
        print("3. Prueba abrir manualmente el PDF")

if __name__ == "__main__":
    main()