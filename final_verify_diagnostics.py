from cargador_universal_gui import ExtractionEngine

def test_final_verification():
    engine = ExtractionEngine()
    # Mocking a typical Gemini output with per-holder sections and totals
    gemini_output = """
#### Consumos Gabriel I Ruiz
01-Jan-25 NETFLIX 15,99
05-Jan-25 AMAZON 45,50
Total 61,49

#### Consumos Marcia M Aguero
10-Jan-25 ZARA 120,00
12-Jan-25 STARBUCKS 12,50
Total 132,50
"""
    items = engine.extraer_gemini_markdown(gemini_output)
    print(f"Items extraídos: {len(items)}")
    
    # Check diagnostics
    for holder, info in engine.diagnostics.items():
        print(f"Holder: {holder}")
        print(f"  ARS Detectado: {info['detectado']['ARS']} | Esperado: {info['esperado']['ARS']}")
        
if __name__ == "__main__":
    test_final_verification()
