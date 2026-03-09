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

def extraer_bbva_refined(texto):
    meses_map_abr = {'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'}
    patron = r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$'
    consumos = []
    for line in texto.split('\n'):
        line = line.strip()
        if not line: continue
        match = re.search(patron, line)
        if match:
            dia, mes_abr, anio, resto = match.groups()
            mes_num = meses_map_abr.get(mes_abr.lower()[:3])
            if not mes_num: continue
            
            limpio = re.sub(r'([A-Za-z])-?(\d+)', r'\1 \2', resto)
            limpio = re.sub(r'([A-Za-z])-(\d+[\.,])', r'\1 -\2', limpio)
            tokens = limpio.split()
            
            monto = None
            monto_idx = -1
            patron_monto = r'^-?[\d\.]+,[0-9]{2}$'
            
            for i in range(len(tokens)-1, -1, -1):
                if re.match(patron_monto, tokens[i]):
                    monto = float(tokens[i].replace('.', '').replace(',', '.'))
                    monto_idx = i
                    break
            
            if monto is None: continue
            desc_raw = " ".join(tokens[:monto_idx])
            moneda = "USD" if "USD" in desc_raw.upper() or "USD" in line.upper() else "ARS"
            vendor_name, cupon, cuotas = clean_vendor_details(desc_raw)
            
            consumos.append({
                "fecha": f"{dia}-{mes_num}-{anio}",
                "descripcion": vendor_name,
                "monto": monto,
                "moneda": moneda
            })
    return consumos

sample = """
09-Ene-26 SU PAGO EN USD-160,00
09-Ene-26 SU PAGO EN PESOS-3.584.432,06
29-Ene-26 DB IVA $ RESP INSC. 21%                  7.128,10 1.496,90
29-Ene-26 PERCEP.IVA RG2408 3,0% B.   7128,10 213,84
16-Ene-26 ADOBE 003198 21.695,30
"""

results = extraer_bbva_refined(sample)
for r in results:
    print(f"{r['fecha']} | {r['moneda']} {r['monto']} | {r['descripcion']}")
