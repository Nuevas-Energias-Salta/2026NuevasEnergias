import pdfplumber
import re

def analyze_bbva_structure():
    """Analiza la estructura específica del PDF de BBVA"""
    
    pdf_path = 'resumenes/Statements (4).pdf'
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Análisis de PDF BBVA: {pdf_path}")
            print(f"Número de páginas: {len(pdf.pages)}")
            print("="*80)
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                print(f"\n--- Página {page_num + 1} ---")
                lines = text.split('\n')
                
                # Buscar secciones clave
                print("\nBUSCANDO SECCIONES:")
                
                for i, line in enumerate(lines):
                    line_upper = line.upper().strip()
                    
                    # Sección DETALLE
                    if "DETALLE" in line_upper:
                        print(f"  * DETALLE encontrado en línea {i+1}: {line}")
                        # Mostrar contexto
                        for j in range(max(0, i-2), min(len(lines), i+10)):
                            marker = ">>>" if j == i else "   "
                            print(f"  {marker} {lines[j].strip()}")
                        print()
                    
                    # Subsecciones CONSUMOS
                    if "CONSUMO" in line_upper:
                        print(f"  * CONSUMOS encontrado en línea {i+1}: {line}")
                        
                    # Subsecciones IMPUESTOS
                    if "IMPUESTO" in line_upper:
                        print(f"  * IMPUESTOS encontrado en línea {i+1}: {line}")
                
                # Buscar patrones de fechas
                print("\nBUSCANDO PATRONES DE FECHAS:")
                date_pattern = r'^(\d{2})-([A-Za-z]{3})-(\d{2})'
                
                for i, line in enumerate(lines):
                    match = re.match(date_pattern, line)
                    if match:
                        print(f"  * Línea {i+1}: {line}")
                        # Mostrar algunas líneas antes y después
                        for j in range(max(0, i-1), min(len(lines), i+2)):
                            marker = ">>>" if j == i else "   "
                            print(f"  {marker} {lines[j].strip()}")
                        print()
                
                # Primeras 20 líneas generales
                print(f"\n📄 PRIMERAS 20 LÍNEAS (página {page_num + 1}):")
                for i, line in enumerate(lines[:20]):
                    print(f"  {i+1:2}: {line}")
                
                print("\n" + "="*80)
    
    except Exception as e:
        print(f"Error analizando PDF: {e}")

if __name__ == "__main__":
    analyze_bbva_structure()