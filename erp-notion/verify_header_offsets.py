import re

def test_header_offsets():
    col_offsets = {"PESOS": -1, "DOLARES": -1}
    
    header = "FECHA DESCRIPCIÓN NRO. CUPÓN PESOS DÓLARES"
    col_offsets["PESOS"] = header.upper().find("PESOS")
    col_offsets["DOLARES"] = header.upper().find("DÓLARES")
    
    print(f"Header offsets: PESOS={col_offsets['PESOS']}, DOLARES={col_offsets['DOLARES']}")
    
    # Simular una línea de ARS (alineada bajo PESOS)
    # FECHA DESCRIPCIÓN NRO. CUPÓN PESOS DÓLARES
    # 06-Ago-25 COMPRA ARS          1.234,56
    line_ars = "06-Ago-25 COMPRA ARS            1.234,56"
    
    # Simular una línea de USD (alineada bajo DÓLARES)
    # FECHA DESCRIPCIÓN NRO. CUPÓN PESOS DÓLARES
    # 06-Ago-25 COMPRA USD                         50,00
    line_usd = "06-Ago-25 COMPRA USD                           50,00"
    
    patron_monto = r'^-?[\d\.]+,[0-9]{2}$'
    
    for line in [line_ars, line_usd]:
        print(f"\nAnalyzing: '{line}'")
        tokens = line.split()
        monto_token = tokens[-1]
        pos_monto = line.rfind(monto_token)
        
        mid = (col_offsets["PESOS"] + col_offsets["DOLARES"]) / 2
        currency = "USD" if pos_monto > mid else "ARS"
        
        print(f"  Monto: {monto_token} at pos {pos_monto}")
        print(f"  Midpoint: {mid}")
        print(f"  Detected Currency: {currency}")

test_header_offsets()
