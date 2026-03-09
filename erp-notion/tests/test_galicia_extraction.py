import re
import json

class MockEngine:
    def __init__(self):
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
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
        desc = re.sub(r'^(MERPAGO\*|MP\*|GOOGLE\*|PAYU\*|MERCADO PAGO\*|\*)', '', desc, flags=re.IGNORECASE).strip()
        vendor_name = desc.replace("*", "").strip()
        if not vendor_name: vendor_name = raw_desc
        return vendor_name, cupon, cuotas

    def extraer_galicia_texto(self, texto):
        patron = r'^(\d{2}-\d{2}-\d{2})\s+(.+?)\s+([0-9\s\.\,]+)$'
        consumos = []
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            if "TOTAL CONSUMOS" in line.upper(): continue
            match = re.search(patron, line)
            if match:
                fecha = match.group(1)
                desc = match.group(2).strip()
                monto_raw = match.group(3).strip()
                try:
                    tokens = monto_raw.split()
                    monto = None
                    for t in reversed(tokens):
                        if ',' in t and re.match(r'^[0-9\.]+,[0-9]{2}$', t):
                            monto = float(t.replace('.', '').replace(',', '.'))
                            break
                    if not monto or monto <= 0: continue
                    moneda = "USD" if "USD" in desc.upper() or "WHATICKET" in desc.upper() or "NOCRM" in desc.upper() else "ARS"
                    vendor_name, cupon, cuotas = self.clean_vendor_details(desc)
                    if cupon == "S/N":
                        for t in tokens:
                            if len(t) == 6 and t.isdigit():
                                cupon = t
                                break
                    consumos.append({
                        "fecha": fecha,
                        "descripcion": vendor_name,
                        "cupon": cupon,
                        "monto": monto,
                        "moneda": moneda,
                        "banco": "GALICIA"
                    })
                except: continue
        return consumos

def test_galicia():
    sample = """
18-01-26 F NOCRM.IO                  USD       32,00 322263 32,00
22-01-26 COMISION RENO.ANUAL(12M) 000000 15.123,00 
08-01-26 * GOMEZ ROCO 000026 681.741,50 
11-01-26 K WHATICKET        in1SoU4VCUSD       49,00 588264 49,00
13-01-26 * FEDERACION PAT0000433799978-004-000 009978 58.855,24 
15-01-26 * FEDERACION PAT0000434855365-004-000 005365 63.370,63 
22-01-26 COMISIÓN MANT DE CTA. 5.289,00 
22-01-26 DB IVA $ RESP INSC. 21%                 20.412,00 4.286,52 
22-01-26 PERCEP.IVA RG2408 3,0% B.  20412,00 612,36 
22-01-26 IIBB PERCEP-SALT 3,60%(  127257,28) 4.581,26 
22-01-26 DB.RG 5617  30% (   560698,78 ) 168.209,63
    """
    engine = MockEngine()
    items = engine.extraer_galicia_texto(sample)
    print(f"Items encontrados: {len(items)}")
    for i in items:
        print(f"{i['fecha']} | {i['moneda']} {i['monto']} | {i['descripcion']} (Cupon: {i['cupon']})")

if __name__ == "__main__":
    test_galicia()
