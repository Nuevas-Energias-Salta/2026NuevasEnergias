from cargador_universal_gui import ExtractionEngine

def test_gemini_parser():
    engine = ExtractionEngine()
    gemini_output = """
#### 2. Consumos Gabriel I Ruiz

| Fecha | Comercio | Nro. Cupon | Cuota | Importe ($) | Importe (US$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 07 Agosto | AEROLINEAS.COM.AR | 009790 | C.18/18 | 11.598,51 | |
| 07 Enero | OPENAI *CHATGPT | 698531 | | | 20,00 |
| *Total* | | | | *11.598,51* | *20,00* |

#### 4. Impuestos y Comisiones

| Fecha | Concepto | Importe ($) |
| :--- | :--- | :--- |
| 22 Enero | COMIS. MANTENIMIENTO | 3.587,00 |
| 22 Enero | DB IVA RESP INSC. 21% | 4.956,34 |
"""
    items = engine.extraer_gemini_markdown(gemini_output)
    print(f"Extracted {len(items)} items:")
    for it in items:
        print(f"[{it['moneda']}] {it['monto']:>10.2f} | {it['fecha']} | {it['descripcion']}")

if __name__ == "__main__":
    test_gemini_parser()
