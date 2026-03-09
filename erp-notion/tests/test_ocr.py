import easyocr
import pypdfium2 as pdfium
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_ocr(pdf_path):
    print(f"Abriendo PDF: {pdf_path}")
    pdf = pdfium.PdfDocument(pdf_path)
    
    print("Inicializando EasyOCR (Español)... esto puede tardar la primera vez...")
    reader = easyocr.Reader(['es'], gpu=False) # GPU False por compatibilidad
    
    for i in range(len(pdf)):
        print(f"\n--- Procesando Página {i+1} ---")
        page = pdf[i]
        bitmap = page.render(scale=2) # 2x scale para mejor calidad
        pil_image = bitmap.to_pil()
        
        # Convertir a bytes para easyocr o pasar path? EasyOCR acepta PIL image?
        # EasyOCR readtext acepta: file path, url, byte, numpy array. 
        # PIL image -> numpy array
        import numpy as np
        image_np = np.array(pil_image)
        
        result = reader.readtext(image_np, detail=0, paragraph=False)
        
        with open("ocr_debug.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- Procesando Página {i+1} ---\n")
            for line in result:
                f.write(line + "\n")
        
        print(f"Página {i+1} procesada y guardada.")

if __name__ == "__main__":
    # Limpiar archivo previo
    open("ocr_debug.txt", "w").close()
    test_ocr("resumenes/descarga.pdf")
