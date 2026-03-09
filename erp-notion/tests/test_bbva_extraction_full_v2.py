import re
import json

class MockEngine:
    def __init__(self):
        self.meses_map = {
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
        }

    def clean_vendor_details(self, raw_desc):
        desc = raw_desc.strip()
        cuotas = ""
        match_cuotas = re.search(r'(C\.\d{2}/\d{2})', desc)
        if match_cuotas:
            cuotas = match_cuotas.group(1)
            desc = desc.replace(cuotas, "").strip()
        cupon = "S/N"
        match_cupon = re.search(r'\b(\d{6})\b', desc)
        if match_cupon:
            cupon = match_cupon.group(1)
            desc = desc.replace(cupon, "").strip()
        desc = re.sub(r'^(MERPAGO\*|MP\*|GOOGLE\*|PAYU\*|MERCADO PAGO\*|\*|F |K )', '', desc, flags=re.IGNORECASE).strip()
        vendor_name = desc.replace("*", "").strip()
        if not vendor_name: vendor_name = raw_desc
        return vendor_name, cupon, cuotas

    def extraer_bbva_texto(self, texto):
        patron = r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$'
        consumos = []
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            if "TOTAL CONSUMOS" in line.upper() or "FECHA" in line[:10].upper(): continue
            match = re.search(patron, line)
            if match:
                dia = match.group( Dia: \d+ )
                dia = match.group(1)
                mes_abr = match.group(2).lower()[:3]
                anio = match.group(3)
                resto = match.group(4).strip()
                mes_num = self.meses_map.get(mes_abr)
                if not mes_num: continue
                try:
                    # Pre-procesar resto para separar montos pegados
                    limpio = re.sub(r'([A-Za-z])-?(\d+)', r'\1 \2', resto)
                    limpio = re.sub(r'([A-Za-z])-(\d+[\.,])', r'\1 -\2', limpio)
                    
                    tokens = limpio.split()
                    if len(tokens) < 1: continue
                    
                    montos_encontrados = []
                    patron_monto = r'^-?[\d\.]+,[0-9]{2}$'
                    
                    for i in range(len(tokens)-1, -1, -1):
                        t = tokens[i]
                        if re.match(patron_monto, t):
                            val = float(t.replace('.', '').replace(',', '.'))
                            montos_encontrados.insert(0, (val, i))
                        else:
                            if len(montos_encontrados) >= 2: break
                            break
                    
                    if not montos_encontrados: continue
                    
                    if len(montos_encontrados) == 2:
                        m_pesos, idx_p = montos_encontrados[0]
                        m_usd, idx_u = montos_encontrados[1]
                        desc_raw = " ".join(tokens[:idx_p])
                        vendor_name, cupon, cuotas = self.clean_vendor_details(desc_raw)
                        if m_pesos != 0:
                            consumos.append({"fecha": f"{dia}-{mes_num}-{anio}", "descripcion": vendor_name, "monto": m_pesos, "moneda": "ARS"})
                        if m_usd != 0:
                            consumos.append({"fecha": f"{dia}-{mes_num}-{anio}", "descripcion": vendor_name, "monto": m_usd, "moneda": "USD"})
                    else:
                        val, idx = montos_encontrados[0]
                        desc_raw = " ".join(tokens[:idx])
                        moneda = "USD" if "USD" in desc_raw.upper() or "USD" in line.upper() else "ARS"
                        vendor_name, cupon, cuotas = self.clean_vendor_details(desc_raw)
                        consumos.append({"fecha": f"{dia}-{mes_num}-{anio}", "descripcion": vendor_name, "monto": val, "moneda": moneda})
                except: continue
        return consumos

def test_bbva_full():
    sample = """
09-Ene-26 SU PAGO EN USD-160,00
09-Ene-26 SU PAGO EN PESOS-3.584.432,06
29-Ene-26 DB IVA $ RESP INSC. 21%                  7.128,10 1.496,90
29-Ene-26 PERCEP.IVA RG2408 3,0% B.   7128,10 213,84
    """
    engine = MockEngine()
    items = engine.extraer_bbva_texto(sample)
    print(f"\nItems encontrados: {len(items)}")
    for i in items:
        print(f"{i['fecha']} | {i['moneda']} {i['monto']} | {i['descripcion']}")

if __name__ == "__main__":
    test_bbva_full()
