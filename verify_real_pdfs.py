import re
import pdfplumber
from cargador_universal_gui import ExtractionEngine

def test_all_banks():
    engine = ExtractionEngine()
    
    files = {
        "MACRO": "resumenes/descarga.pdf",
        "GALICIA": "resumenes/Resumen_Tarjetas_Galicia_2026_01_22.pdf",
        "BBVA": "resumenes/Statements (4).pdf"
    }
    
    for banco, path in files.items():
        print(f"\n{'='*20} {banco} {'='*20}")
        try:
            with pdfplumber.open(path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
            
            if banco == "MACRO":
                items = engine.extraer_macro_texto(full_text)
            elif banco == "GALICIA":
                items = engine.extraer_galicia_texto(full_text)
            elif banco == "BBVA":
                items = engine.extraer_bbva_texto(full_text)
            
            print(f"Encontrados: {len(items)} items")
            # Mostrar los primeros 10 para no saturar
            for i, item in enumerate(items[:10]):
                print(f"[{i+1}] {item['fecha']} | {item['moneda']} {item['monto']:>10.2f} | {item['descripcion']} (Cupón: {item.get('cupon', 'S/N')})")
                
            # Buscar un ejemplo de USD específicamente en cada banco
            usd_items = [it for it in items if it['moneda'] == "USD"]
            if usd_items:
                print(f"\n--- Ejemplo USD detectado en {banco} ---")
                print(f"  {usd_items[0]['fecha']} | {usd_items[0]['moneda']} {usd_items[0]['monto']} | {usd_items[0]['descripcion']}")
            else:
                print(f"\n(No se detectaron items USD en este bloque de {banco})")
                
        except Exception as e:
            print(f"Error procesando {banco}: {e}")

if __name__ == "__main__":
    test_all_banks()
