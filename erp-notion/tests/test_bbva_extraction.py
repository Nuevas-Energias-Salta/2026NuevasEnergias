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
                dia = match.group(1)
                mes_abr = match.group(2).lower()[:3]
                anio = match.group(3)
                resto = match.group(4).strip()
                mes_num = self.meses_map.get(mes_abr)
                if not mes_num: continue
                try:
                    tokens = resto.split()
                    if len(tokens) < 2: continue
                    monto = None
                    monto_idx = -1
                    for i in range(len(tokens)-1, -1, -1):
                        t = tokens[i]
                        if ',' in t and re.match(r'^[0-9\.]+,[0-9]{2}$', t):
                            val = float(t.replace('.', '').replace(',', '.'))
                            if val > 0:
                                monto = val
                                monto_idx = i
                                break
                    if not monto: continue
                    cupon = "S/N"
                    if monto_idx > 0:
                        potential_cupon = tokens[monto_idx - 1]
                        if potential_cupon.isdigit() and len(potential_cupon) >= 4:
                            cupon = potential_cupon
                    limit = monto_idx - 1 if cupon != "S/N" else monto_idx
                    desc_raw = " ".join(tokens[:limit])
                    moneda = "USD" if "USD" in desc_raw.upper() or "ADOBE" in desc_raw.upper() else "ARS"
                    vendor_name, v_cupon, cuotas = self.clean_vendor_details(desc_raw)
                    if v_cupon != "S/N": cupon = v_cupon
                    consumos.append({
                        "fecha": f"{dia}-{mes_num}-{anio}",
                        "descripcion": vendor_name,
                        "cupon": cupon,
                        "monto": monto,
                        "moneda": moneda,
                        "banco": "BBVA"
                    })
                except: continue
        return consumos

def test_bbva():
    sample = """
06-Ago-25 MERPAGO*ALWAYSRENTACA       C.06/06 858124 18.248,33
07-Ago-25 MERPAGO*ALWAYSRENTACA       C.06/06 549977 18.248,33
03-Sep-25 MERPAGO*ALWAYSRENTACA       C.05/06 328822 33.593,53
16-Ene-26 ADOBE 003198 21.695,30
22-Ene-26 SANCOR COOP SE0000099309667-060-000 005902 10.149,00
25-Ene-26 CABLE EXPRESS    000000000316256 000001 72.888,20
27-Ene-26 MERPAGO*CALZETTANEUMA 024871 151.966,00
    """
    engine = MockEngine()
    items = engine.extraer_bbva_texto(sample)
    print(f"Items encontrados: {len(items)}")
    for i in items:
        print(f"{i['fecha']} | {i['moneda']} {i['monto']} | {i['descripcion']} (Cupon: {i['cupon']})")

if __name__ == "__main__":
    test_bbva()
