import pdfplumber

# Extraer y mostrar el texto para entender la estructura
ruta_pdf = r"C:\Users\Gonza\Desktop\Notion-project\resumenes\descarga.pdf"

with pdfplumber.open(ruta_pdf) as pdf:
    print(f"Páginas: {len(pdf.pages)}")
    
    for i, pagina in enumerate(pdf.pages):
        print(f"\n--- PÁGINA {i+1} ---")
        print(f"Dimensiones: {pagina.width} x {pagina.height}")
        
        # Extraer texto
        texto = pagina.extract_text()
        print(f"Texto: {'SÍ' if texto else 'NO'}")
        if texto:
            print("Primeras líneas:")
            for j, linea in enumerate(texto.split('\n')[:10], 1):
                print(f"{j:2d}: {linea}")
        
        # Extraer caracteres individuales
        chars = pagina.chars
        print(f"Caracteres encontrados: {len(chars)}")
        if chars:
            print("Primeros 5 caracteres:")
            for char in chars[:5]:
                print(f"  '{char['text']}' at ({char['x0']}, {char['y0']})")
        
        # Extraer palabras
        words = pagina.extract_words()
        print(f"Palabras encontradas: {len(words)}")
        if words:
            print("Primeras 5 palabras:")
            for word in words[:5]:
                print(f"  '{word['text']}' at ({word['x0']}, {word['top']})")