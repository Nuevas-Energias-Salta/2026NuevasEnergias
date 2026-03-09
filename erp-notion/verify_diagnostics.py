from cargador_universal_gui import ExtractionEngine

def test_diagnostics():
    engine = ExtractionEngine()
    gemini_text = """
#### 2. Consumos Gabriel I Ruiz
03-Sep-24 ENERGE S.A. 274.506,00
11-Sep-24 ENERGE S.A. 210.783,04
Total 485.289,04

#### 3. Consumos MARCIA M AGUERO
22-Sep-24 OPENAI USD 20,00 18.000,00 20,00
Total 18.000,00 20,00
"""
    items = engine.extraer_gemini_markdown(gemini_text)
    print(f"Items extraídos: {len(items)}")
    for tit, data in engine.diagnostics.items():
        print(f"\nTitular: {tit}")
        print(f"  Diferencia ARS: {data['detectado']['ARS']} vs Esperado {data['esperado']['ARS']}")
        print(f"  Diferencia USD: {data['detectado']['USD']} vs Esperado {data['esperado']['USD']}")

if __name__ == "__main__":
    test_diagnostics()
