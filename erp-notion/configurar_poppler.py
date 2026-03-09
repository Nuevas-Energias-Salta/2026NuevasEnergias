#!/usr/bin/env python3
"""
Configurar y ejecutar extracción de PDF de Banco Macro
"""
import os
import sys
import subprocess

def setup_poppler():
    """
    Configura la ruta de Poppler automáticamente
    """
    # Posibles rutas de instalación de Poppler en Windows
    possible_paths = [
        r"C:\Program Files\poppler-24.02.0\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler-24.02.0\Library\bin",
        r"C:\poppler-24.02.0\Library\bin",
        r"C:\tools\poppler\bin",
        os.path.expanduser("~/poppler-24.02.0/Library/bin"),
    ]
    
    poppler_path = None
    for path in possible_paths:
        if os.path.exists(path):
            poppler_path = path
            print(f"OK - Poppler encontrado en: {path}")
            break
    
    if poppler_path:
        # Añadir al PATH
        current_path = os.environ.get('PATH', '')
        if poppler_path not in current_path:
            os.environ['PATH'] = poppler_path + os.pathsep + current_path
            print(f"OK - Poppler añadido al PATH")
        return True
    else:
        print("X - Poppler no encontrado en las rutas comunes")
        print("Por favor, especifica la ruta manualmente:")
        print("Ej: C:\\Users\\TuUsuario\\Downloads\\poppler-24.02.0\\Library\\bin")
        
        # Pedir ruta al usuario
        manual_path = input("Ingresa la ruta donde está poppler: ").strip()
        if manual_path and os.path.exists(manual_path):
            os.environ['PATH'] = manual_path + os.pathsep + os.environ.get('PATH', '')
            print(f"OK - Poppler configurado manualmente en: {manual_path}")
            return True
        return False

def test_poppler():
    """
    Prueba si Poppler está funcionando
    """
    try:
        result = subprocess.run(['pdftotext', '-v'], 
                              capture_output=True, text=True, check=True)
        print(f"OK - pdftotext funcionando: {result.stdout.split()[2]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("X - pdftotext no está funcionando correctamente")
        return False

def extract_pdf_with_poppler(pdf_path):
    """
    Extrae texto del PDF usando Poppler
    """
    print(f"\n=== EXTRAYENDO TEXTO DE: {pdf_path} ===")
    
    # Método 1: Layout (mejor para tablas)
    output_layout = f"resumenes/extraido_layout.txt"
    cmd_layout = ['pdftotext', '-layout', '-enc', 'UTF-8', pdf_path, output_layout]
    
    # Método 2: Table (optimizado para tablas)
    output_table = f"resumenes/extraido_table.txt"
    cmd_table = ['pdftotext', '-table', '-enc', 'UTF-8', pdf_path, output_table]
    
    # Método 3: Simple
    output_simple = f"resumenes/extraido_simple.txt"
    cmd_simple = ['pdftotext', '-simple', '-enc', 'UTF-8', pdf_path, output_simple]
    
    methods = [
        ("Layout", cmd_layout, output_layout),
        ("Table", cmd_table, output_table),
        ("Simple", cmd_simple, output_simple)
    ]
    
    results = {}
    
    for method_name, cmd, output_file in methods:
        print(f"\nProbando método: {method_name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = [line for line in content.split('\n') if line.strip()]
                results[method_name] = {
                    'content': content,
                    'lines': lines,
                    'file': output_file
                }
                
                print(f"OK - {len(lines)} líneas extraídas")
                
                # Mostrar primeras 3 líneas si hay contenido
                if lines:
                    print("Primeras líneas:")
                    for i, line in enumerate(lines[:3]):
                        print(f"  {i+1}: {repr(line)}")
                else:
                    print("  (Sin contenido visible)")
            else:
                print(f"X - No se generó archivo: {output_file}")
                
        except subprocess.CalledProcessError as e:
            print(f"X - Error: {e.stderr}")
    
    return results

def analyze_best_result(results):
    """
    Analiza cuál método dio mejores resultados
    """
    if not results:
        print("\nX - Ningún método logró extraer contenido")
        return None
    
    print("\n=== ANÁLISIS DE RESULTADOS ===")
    
    best_method = None
    max_lines = 0
    
    for method_name, result in results.items():
        line_count = len(result['lines'])
        print(f"{method_name}: {line_count} líneas")
        
        if line_count > max_lines:
            max_lines = line_count
            best_method = method_name
    
    if best_method and max_lines > 0:
        print(f"\nOK - Mejor método: {best_method} ({max_lines} líneas)")
        return results[best_method]
    else:
        print("\nX - Todos los métodos fallaron")
        return None

def main():
    print("=== EXTRACCIÓN PDF BANCO MACRO CON POPPLER ===")
    
    # 1. Configurar Poppler
    if not setup_poppler():
        print("\nX - No se puede continuar sin Poppler")
        return
    
    # 2. Probar Poppler
    if not test_poppler():
        print("\nX - Poppler no está funcionando")
        return
    
    # 3. Extraer del PDF
    pdf_path = "resumenes/descarga.pdf"
    if not os.path.exists(pdf_path):
        print(f"\nX - No se encuentra el PDF: {pdf_path}")
        return
    
    results = extract_pdf_with_poppler(pdf_path)
    
    # 4. Analizar resultados
    best_result = analyze_best_result(results)
    
    if best_result:
        # Guardar el mejor resultado como principal
        main_file = "resumenes/macro_mejor_extraccion.txt"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(best_result['content'])
        
        print(f"\nOK - Mejor resultado guardado en: {main_file}")
        print(f"OK - Total de líneas: {len(best_result['lines'])}")
        
        # Mostrar estadísticas
        total_chars = len(best_result['content'])
        print(f"OK - Total de caracteres: {total_chars}")
        
        if total_chars > 100:  # Si hay contenido significativo
            print("\n¡Extracción exitosa! Ahora puedes procesar este texto.")
        else:
            print("\n! El contenido es muy limitado, puede requerir OCR")

if __name__ == "__main__":
    main()