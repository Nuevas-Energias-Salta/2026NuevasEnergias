import re
import json

def test_extraction():
    meses_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
    }

    # Regex mejorada
    patron = r'^(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+(\d{2,4}))?\s+(.+?)\s+([0-9\s\.\,]+)$'
    
    with open('pegar_resumen_aqui.txt', 'r', encoding='utf-8') as f:
        texto = f.read()

    consumos = []
    lineas = texto.split('\n')
    print(f"Procesando {len(lineas)} líneas...")

    for line in lineas:
        line = line.strip()
        if not line: continue
        
        if line.upper().startswith("TARJETA") and "TOTAL CONSUMOS" in line.upper():
            continue
            
        match = re.search(patron, line)
        if match:
            raw_dia = match.group(1).zfill(2)
            raw_mes = match.group(2).lower()
            raw_anio = match.group(3) or "26"
            desc = match.group(4).strip()
            monto_raw = match.group(5).strip()
            
            mes_num = meses_map.get(raw_mes)
            if not mes_num: 
                # print(f"Mes no reconocido: {raw_mes} en linea: {line}")
                continue
            
            try:
                monto_tokens = monto_raw.split()
                monto_str = monto_tokens[-1]
                monto = float(monto_str.replace('.', '').replace(',', '.'))
                
                if monto <= 0: continue
                
                moneda = "USD" if "USD" in desc.upper() or "OPENAI" in desc.upper() else "ARS"
                
                consumos.append({
                    "fecha": f"{raw_dia}-{mes_num}-{raw_anio}",
                    "descripcion": desc,
                    "monto": monto,
                    "moneda": moneda
                })
            except Exception as e:
                print(f"Error procesando monto: {monto_raw} -> {e}")
        else:
            # print(f"Línea no coincide: {line}")
            pass

    print(f"\nFinalizado. Se encontraron {len(consumos)} consumos.")
    for i, c in enumerate(consumos[:10], 1):
        print(f"{i}. {c['fecha']} | {c['monto']} | {c['descripcion']}")
    
    if len(consumos) > 0:
        with open('test_output.json', 'w', encoding='utf-8') as f:
            json.dump(consumos, f, indent=2, ensure_ascii=False)
        print("\nResultados guardados en test_output.json")

if __name__ == "__main__":
    test_extraction()
