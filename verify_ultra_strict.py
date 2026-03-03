import re
from cargador_universal_gui import ExtractionEngine

def test_ultra_strict():
    engine = ExtractionEngine()
    
    # 1. BBVA Simulation (Based on User Image)
    # FECHA     DESCRIPCIÓN                   NRO. CUPÓN     PESOS      DÓLARES
    bbva_text = """
FECHA     DESCRIPCIÓN                   NRO. CUPÓN     PESOS      DÓLARES
06-Ago-25 MERPAGO*ALWAYSRENTACA C.06/05     858124      18.248,33
TOTAL CONSUMOS DE AGUSTIN ISASMENDI                    599.536,76       0,00
"""
    print("--- Testing BBVA ---")
    items = engine.extraer_bbva_texto(bbva_text)
    for it in items:
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['descripcion']}")

    # 4. Multi-page Persistence Test
    print("\n--- Testing Multi-page Persistence ---")
    page1 = """
FECHA    REFERENCIA            CUOTA  COMPROBANTE   PESOS                   DÓLARES
12-05-25 R MERPAGO*OVERHARD       09/18   486050    110.888,83
"""
    page2 = """
28-12-25 K OPENAI *CHATGPT in15 USD 20,00         328822                    20,00
"""
    # Simulate first page (detects header)
    items1 = engine.extraer_galicia_texto(page1)
    # Simulate second page (should keep header from engine state)
    items2 = engine.extraer_galicia_texto(page2)
    
    for it in items1 + items2:
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['descripcion']}")

if __name__ == "__main__":
    test_ultra_strict()
