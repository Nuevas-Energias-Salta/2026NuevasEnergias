import re

class ColumnParser:
    def __init__(self, header_text):
        self.header_text = header_text
        self.columns = {}
        # Encontrar posiciones de headers clave
        for key in ["FECHA", "DESCRIPCIÓN", "DESCRIPCION", "CUPÓN", "CUPON", "PESOS", "DÓLARES", "DOLARES"]:
            pos = header_text.find(key)
            if pos != -1:
                # Normalizar keys
                norm_key = key.replace("Ó", "O").replace("Ú", "U")
                self.columns[norm_key] = pos
        print(f"Detected columns: {self.columns}")

    def parse_line(self, line):
        # Encontrar todos los números con coma (montos)
        matches = list(re.finditer(r'-?[\d\.]+,[0-9]{2}', line))
        results = []
        
        pos_pesos = self.columns.get("PESOS", -1)
        pos_dolares = self.columns.get("DOLARES", -1)
        
        # Heurística: Si no hay headers claros, el último es USD si hay gran espacio antes.
        for m in matches:
            val = m.group()
            pos = m.start()
            
            currency = "ARS"
            if pos_pesos != -1 and pos_dolares != -1:
                # Comparar distancias a los headers
                dist_p = abs(pos - pos_pesos)
                dist_d = abs(pos - pos_dolares)
                if dist_d < dist_p or pos > (pos_pesos + pos_dolares)/2:
                    currency = "USD"
            
            results.append({"val": val, "currency": currency, "pos": pos})
        return results

def test_v3():
    header_bbva = "FECHA DESCRIPCIÓN NRO. CUPÓN PESOS DÓLARES"
    parser = ColumnParser(header_bbva)
    
    lines = [
        "29-Ene-26 DB IVA $ RESP INSC. 21%                  7.128,10 1.496,90",
        "29-Ene-26 PERCEP.IVA RG2408 3,0% B.   7128,10 213,84",
        "06-Ago-25 MERPAGO*ALWAYSRENTACA       C.06/06 858124 18.248,33",
        "09-Ene-26 SU PAGO EN USD-160,00"
    ]
    
    for l in lines:
        print(f"\nParsing: {l}")
        res = parser.parse_line(l)
        for r in res:
            print(f"  -> {r['currency']}: {r['val']} (pos {r['pos']})")

test_v3()
