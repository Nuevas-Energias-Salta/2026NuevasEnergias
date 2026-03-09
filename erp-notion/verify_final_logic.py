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
    desc = re.sub(r'\s*(?:USD|ARS|ARS\$|\$)?\s*\d+[\d\.]*,[0-9]{2}$', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'\s+USD\s*$', '', desc, flags=re.IGNORECASE).strip()
    vendor_name = desc.replace("*", "").strip()
    return vendor_name, cupon, cuotas

def extraer_galicia(texto):
    patron = r'^(\d{2}-\d{2}-\d{2})\s+(.+)$'
    for line in texto.split('\n'):
        if not line.strip(): continue
        match = re.search(patron, line)
        if match:
            fecha, resto = match.groups()
            tokens = resto.strip().split()
            monto = None
            for i in range(len(tokens)-1, -1, -1):
                if ',' in tokens[i] and re.match(r'^-?[\d\.]+,[0-9]{2}$', tokens[i]):
                    monto = tokens[i]
                    monto_idx = i
                    break
            if monto:
                moneda = "USD" if "USD" in line.upper() else "ARS"
                desc = " ".join(tokens[:monto_idx])
                name, cup, cuo = clean_vendor_details(desc)
                print(f"GALICIA: {fecha} | {moneda} {monto} | {name} | Cupón: {cup}")

def extraer_bbva(texto):
    patron = r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$'
    for line in texto.split('\n'):
        if not line.strip(): continue
        match = re.search(patron, line)
        if match:
            dia, mes, anio, resto = match.groups()
            tokens = resto.strip().split()
            monto = None
            for i in range(len(tokens)-1, -1, -1):
                if ',' in tokens[i] and re.match(r'^-?[\d\.]+,[0-9]{2}$', tokens[i]):
                    monto = tokens[i]
                    monto_idx = i
                    break
            if monto:
                moneda = "USD" if "USD" in line.upper() else "ARS"
                desc = " ".join(tokens[:monto_idx])
                name, cup, cuo = clean_vendor_details(desc)
                print(f"BBVA: {dia}-{mes}-{anio} | {moneda} {monto} | {name}")

galicia_sample = "18-01-26 F NOCRM.IO                  USD       32,00 322263 32,00"
bbva_sample = "16-Ene-26 ADOBE 003198 21.695,30"

print("--- RESULTADOS FINALES ---")
extraer_galicia(galicia_sample)
extraer_bbva(bbva_sample)
