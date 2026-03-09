import re

def analyze_columns(header, line):
    # Encontrar posiciones de las palabras clave en la cabecera
    pos_pesos = header.find("PESOS")
    pos_dolares = header.find("DÓLARES")
    if pos_dolares == -1: pos_dolares = header.find("DOLARES")
    
    print(f"Header: {header}")
    print(f"PESOS at {pos_pesos}, DOLARES at {pos_dolares}")
    
    # Encontrar todos los montos en la línea y sus posiciones
    matches = list(re.finditer(r'-?[\d\.]+,[0-9]{2}', line))
    results = []
    
    for m in matches:
        val_str = m.group()
        start = m.start()
        end = m.end()
        # Determinar a qué columna pertenece basándose en la proximidad o en el espaciado
        # Si hay un gran espacio antes, o si está cerca de la posición del header
        dist_pesos = abs(start - pos_pesos)
        dist_dolares = abs(start - pos_dolares)
        
        print(f"Token '{val_str}' at [{start}:{end}] (dist_P: {dist_pesos}, dist_D: {dist_dolares})")
        
        # Una regla empírica: si está más a la derecha que el medio entre ambos headers
        mid = (pos_pesos + pos_dolares) / 2
        if start > mid:
            currency = "USD"
        else:
            currency = "ARS"
            
        # Pero si solo hay un monto y está muy a la derecha...
        # A veces el texto copiado colapsa espacios.
        results.append((val_str, currency, start))
    
    return results

header_bbva = "FECHA DESCRIPCIÓN NRO. CUPÓN PESOS DÓLARES"
sample_lines = [
    "06-Ago-25 MERPAGO*ALWAYSRENTACA       C.06/06 858124 18.248,33",
    "29-Ene-26 DB IVA $ RESP INSC. 21%                  7.128,10 1.496,90",
    "29-Ene-26 PERCEP.IVA RG2408 3,0% B.   7128,10 213,84",
    "TOTAL CONSUMOS DE AGUSTIN ISASMENDI 559.536,76 0,00"
]

print("--- ANALIZANDO BBVA ---")
for line in sample_lines:
    print(f"\nLine: {line}")
    res = analyze_columns(header_bbva, line)
    for v, c, s in res:
        print(f"  -> {c}: {v}")

header_impuestos = "FECHA DESCRIPCIÓN PESOS DÓLARES"
print("\n--- ANALIZANDO IMPUESTOS ---")
for line in sample_lines[1:]:
    print(f"\nLine: {line}")
    res = analyze_columns(header_impuestos, line)
    for v, c, s in res:
        print(f"  -> {c}: {v}")
