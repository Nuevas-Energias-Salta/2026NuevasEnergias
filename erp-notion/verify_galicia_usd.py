import re

def clean_vendor_details(raw_desc):
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
    return vendor_name, cupon, cuotas

def extraer_galicia_texto(texto):
    patron = r'^(\d{2}-\d{2}-\d{2})\s+(.+)$'
    consumos = []
    for line in texto.split('\n'):
        line = line.strip()
        if not line: continue
        if "TOTAL CONSUMOS" in line.upper(): continue
        match = re.search(patron, line)
        if match:
            fecha = match.group(1)
            resto = match.group(2).strip()
            tokens = resto.split()
            monto = None
            monto_idx = -1
            for i in range(len(tokens)-1, -1, -1):
                t = tokens[i]
                if ',' in t and re.match(r'^-?[\d\.]+,[0-9]{2}$', t):
                    monto = float(t.replace('.', '').replace(',', '.'))
                    monto_idx = i
                    break
            if monto is None: continue
            moneda = "USD" if "USD" in line.upper() else "ARS"
            desc = " ".join(tokens[:monto_idx])
            vendor_name, cupon, cuotas = clean_vendor_details(desc)
            if cupon == "S/N":
                for t in tokens[monto_idx+1:]:
                    if len(t) == 6 and t.isdigit():
                        cupon = t
                        break
            consumos.append({
                "fecha": fecha,
                "descripcion": vendor_name,
                "monto": monto,
                "moneda": moneda,
                "cupon": cupon
            })
    return consumos

sample = """
18-01-26 F NOCRM.IO                  USD       32,00 322263 32,00
11-01-26 K WHATICKET        in1SoU4VCUSD 49,00 588264 49,00
13-01-26 FEDERACION PAT0000433799978-004-000 58.855,24 009978 58.855,24
"""

results = extraer_galicia_texto(sample)
for r in results:
    print(f"{r['fecha']} | {r['moneda']} {r['monto']} | {r['descripcion']} | Cupón: {r['cupon']}")
