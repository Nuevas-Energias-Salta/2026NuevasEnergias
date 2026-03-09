from cargador_universal_gui import ExtractionEngine
import json

def verify_macro():
    engine = ExtractionEngine()
    with open('pegar_resumen_aqui.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # We use extraer_macro_texto but it doesn't currently handle holders by default 
    # unless we use the Gemini path. 
    # Let's see if we should use the Gemini path or the raw Macro path.
    # The user is asking about "Verifying Macro" - usually they mean the raw OCR/Text path.
    # But I recently added titular grouping to extraer_gemini_markdown.
    
    # Let's try raw Macro extraction first.
    items = engine.extraer_macro_texto(text)
    
    print(f"--- Extracción RAW MACRO (Con Titulares) ---")
    print(f"Total items: {len(items)}")
    for it in items:
        tit = it.get('titular', 'N/A')
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['fecha']} | {it['descripcion'][:20]:<20} | {tit}")
    
    if hasattr(engine, 'diagnostics'):
        print("\n--- Diagnósticos Macro ---")
        print(json.dumps(engine.diagnostics, indent=2))

    # Now let's try the Gemini path with this same text to see if it groups them.
    # Note: the raw text in pegar_resumen_aqui.txt IS NOT Markdown, but I added smashed support.
    items_gemini = engine.extraer_gemini_markdown(text)
    
    print(f"\n--- Extracción GEMINI / SMASHED (Con Titulares) ---")
    print(f"Total items: {len(items_gemini)}")
    for it in items_gemini:
        tit = it.get('titular', 'N/A')
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['fecha']} | {it['descripcion'][:20]:<20} | {tit}")
    
    if hasattr(engine, 'diagnostics'):
        print("\n--- Diagnósticos ---")
        print(json.dumps(engine.diagnostics, indent=2))

if __name__ == "__main__":
    verify_macro()
