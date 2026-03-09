import pdfplumber

# Analizar estructura del PDF de Galicia
pdf_path = 'resumenes/Resumen_Tarjetas_Galicia_2026_01_22.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    
    print("="*80)
    print("ESTRUCTURA DEL RESUMEN GALICIA")
    print("="*80)
    
    lines = text.split('\n')
    
    # Buscar la sección "DETALLE DEL CONSUMO"
    in_detail = False
    print("\nBUSCANDO SECCIÓN 'DETALLE DEL CONSUMO':\n")
    
    for i, line in enumerate(lines):
        if "DETALLE DEL CONSUMO" in line:
            in_detail = True
            print(f"Línea {i}: {line}")
            print("\nEncabezado de columnas:")
            if i+1 < len(lines):
                print(f"Línea {i+1}: {lines[i+1]}")
            print("\nPrimeras 15 líneas de consumos:")
            print("-"*80)
            
            # Mostrar las siguientes líneas de consumo
            for j in range(i+2, min(i+17, len(lines))):
                if lines[j].strip():
                    print(f"{j-i-1:2}. {lines[j]}")
            break
    
    print("\n" + "="*80)
    print("ANÁLISIS DE COLUMNAS")
    print("="*80)
    
    # Analizar líneas con fecha al inicio
    print("\nEjemplos de líneas con formato DD-MM-YY:\n")
    
    import re
    count = 0
    for line in lines:
        match = re.match(r'^(\d{2}-\d{2}-\d{2})\s+(.+)$', line)
        if match and count < 10:
            fecha = match.group(1)
            resto = match.group(2)
            
            # Analizar tokens
            tokens = resto.split()
            
            print(f"\n{count+1}. Fecha: {fecha}")
            print(f"   Línea completa: {line[:100]}")
            print(f"   Tokens: {tokens}")
            print(f"   Último token (monto?): {tokens[-1] if tokens else 'N/A'}")
            
            # Detectar si tiene USD
            has_usd = 'USD' in line
            print(f"   Tiene USD: {has_usd}")
            
            count += 1

print("\n" + "="*80)
print("RECOMENDACIONES:")
print("="*80)
print("""
Para corregir la extracción necesitamos:

1. Identificar la estructura exacta de columnas
2. Ver si hay diferencia entre líneas ARS y USD
3. Asegurar que tomamos el monto correcto (columna PESOS o DÓLARES)
4. Verificar que no estamos tomando números de cupón como montos
""")
