import pdfplumber
import re
from pathlib import Path

def analizar_pdf_tarjetas_galicia(pdf_path):
    """Analiza el PDF de resumen de tarjetas Galicia para extraer información estructurada"""
    
    print(f"Analizando PDF: {pdf_path.name}")
    print("=" * 80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Número de páginas: {len(pdf.pages)}")
            print()
            
            # Extraer texto de todas las páginas
            texto_completo = ""
            for i, page in enumerate(pdf.pages):
                print(f"--- Página {i+1} ---")
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n\n"
                    print(texto_pagina[:500] + "..." if len(texto_pagina) > 500 else texto_pagina)
                print()
            
            print("=" * 80)
            print("ANALISIS DE CONTENIDO")
            print("=" * 80)
            
            # 1. Buscar período de facturación
            print("\n1. PERIODO DE FACTURACION:")
            patron_periodo = r'(?:Período|Periodo|Facturación|Resumen).*?(\d{2}[\/\-]\d{2}[\/\-]\d{4}).*?(\d{2}[\/\-]\d{2}[\/\-]\d{4})'
            periodos = re.findall(patron_periodo, texto_completo, re.IGNORECASE)
            
            if periodos:
                for i, (inicio, fin) in enumerate(periodos):
                    print(f"   * Período {i+1}: {inicio} → {fin}")
            else:
                # Buscar fechas individuales
                fechas = re.findall(r'\d{2}[\/\-]\d{2}[\/\-]\d{4}', texto_completo)
                if fechas:
                    print(f"   * Fechas encontradas: {fechas}")
                else:
                    print("   * No se encontraron períodos claros")
            
            # 2. Identificar secciones principales
            print("\n2. SECCIONES PRINCIPALES:")
            
            # Buscar palabras clave de secciones
            secciones_interes = [
                "Resumen del Período Actual",
                "Resumen del Periodo Actual", 
                "Resumen Período Actual",
                "Consumos del Período",
                "Consumos del Periodo",
                "Otros Conceptos",
                "Resumen Mes",
                "Detalle de Consumos",
                "Movimientos del Período",
                "Compras del Período",
                "Liquidación del Período"
            ]
            
            lineas = texto_completo.split('\n')
            for seccion in secciones_interes:
                for i, linea in enumerate(lineas):
                    if re.search(seccion, linea, re.IGNORECASE):
                        print(f"   * '{seccion}' encontrada en línea {i+1}: {linea.strip()}")
                        # Mostrar contexto
                        contexto_inicio = max(0, i-2)
                        contexto_fin = min(len(lineas), i+5)
                        print("     Contexto:")
                        for j in range(contexto_inicio, contexto_fin):
                            prefijo = ">>>" if j == i else "   "
                            print(f"     {prefijo} {lineas[j].strip()}")
                        print()
            
            # 3. Buscar información de períodos actual vs anteriores
            print("\n3. DISTINCION PERIODOS ACTUAL vs ANTERIORES:")
            
            patron_actual = r'(?:actual|presente|corriente|mes actual|este mes)'
            patron_anterior = r'(?:anterior|pasado|mes anterior|período anterior)'
            
            lineas_actual = []
            lineas_anterior = []
            
            for i, linea in enumerate(lineas):
                if re.search(patron_actual, linea, re.IGNORECASE):
                    lineas_actual.append((i+1, linea.strip()))
                if re.search(patron_anterior, linea, re.IGNORECASE):
                    lineas_anterior.append((i+1, linea.strip()))
            
            if lineas_actual:
                print("   * Referencias al período ACTUAL:")
                for num_linea, linea in lineas_actual[:5]:  # Limitar a primeras 5
                    print(f"     Línea {num_linea}: {linea}")
            
            if lineas_anterior:
                print("   * Referencias a períodos ANTERIORES:")
                for num_linea, linea in lineas_anterior[:5]:  # Limitar a primeras 5
                    print(f"     Línea {num_linea}: {linea}")
            
            # 4. Buscar información de consumos separados
            print("\n4. INFORMACION DE CONSUMOS:")
            
            # Buscar patrones de consumos
            patron_consumo = r'(?:compra|consumo|gasto|débito|cargo).*?\$?[\d.,]+'
            consumos = re.findall(patron_consumo, texto_completo, re.IGNORECASE)
            
            if consumos:
                print(f"   * Se encontraron {len(consumos)} referencias a consumos:")
                for consumo in consumos[:10]:  # Primeras 10
                    print(f"     - {consumo}")
            
            # 5. Extraer tablas si existen
            print("\n5. TABLAS ENCONTRADAS:")
            
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    print(f"   * Página {i+1}: {len(tables)} tabla(s)")
                    for j, table in enumerate(tables[:2]):  # Mostrar primeras 2 tablas
                        print(f"     Tabla {j+1}:")
                        if table and len(table) > 0:
                            # Mostrar encabezado y primeras filas
                            for row_idx, row in enumerate(table[:5]):
                                if row:
                                    row_clean = [str(cell) if cell else "" for cell in row]
                                    print(f"       {row_idx+1}: {' | '.join(row_clean)}")
                            if len(table) > 5:
                                print(f"       ... ({len(table)-5} filas más)")
                        print()
            
            return {
                'total_paginas': len(pdf.pages),
                'texto_completo': texto_completo,
                'periodos_encontrados': periodos,
                'secciones_encontradas': len([s for s in secciones_interes if any(re.search(s, linea, re.IGNORECASE) for linea in lineas)]),
                'tiene_tablas': any(len(page.extract_tables()) > 0 for page in pdf.pages)
            }
            
    except Exception as e:
        print(f"❌ Error al procesar el PDF: {e}")
        return None

# Analizar el PDF específico
pdf_path = Path("resumenes/Resumen_Tarjetas_Galicia_2026_01_22.pdf")

if pdf_path.exists():
    resultado = analizar_pdf_tarjetas_galicia(pdf_path)
    
    if resultado:
        print("\n" + "=" * 80)
        print("RESUMEN DEL ANALISIS")
        print("=" * 80)
        print(f"* Total páginas: {resultado['total_paginas']}")
        print(f"* Períodos encontrados: {len(resultado['periodos_encontrados'])}")
        print(f"* Secciones relevantes: {resultado['secciones_encontradas']}")
        print(f"* Contiene tablas: {'Sí' if resultado['tiene_tablas'] else 'No'}")
else:
    print(f"No se encontró el archivo: {pdf_path}")