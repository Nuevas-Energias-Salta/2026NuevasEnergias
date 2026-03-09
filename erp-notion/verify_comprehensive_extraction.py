import re

class MockExtractor:
    def __init__(self):
        self.meses_map = {
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
            'marzo': '03', 'agosto': '08', 'abril': '04'
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
        desc = re.sub(r'\s*(?:USD|ARS|ARS\$|\$)?\s*\d+[\d\.]*,[0-9]{2}$', '', desc, flags=re.IGNORECASE).strip()
        desc = re.sub(r'\s+USD\s*$', '', desc, flags=re.IGNORECASE).strip()
        vendor_name = desc.replace("*", "").strip()
        return vendor_name, cupon, cuotas

    def _parse_columnar_line(self, line, fecha, banco):
        limpio = re.sub(r'([A-Za-z])-?(\d+)', r'\1 \2', line)
        limpio = re.sub(r'([A-Za-z])-(\d+[\.,])', r'\1 -\2', limpio)
        tokens = limpio.split()
        if len(tokens) < 2: return []
        montos = []
        desc_end_idx = len(tokens)
        patron_monto = r'^-?[\d\.]+,[0-9]{2}$'
        for i in range(len(tokens)-1, -1, -1):
            t = tokens[i]
            if re.match(patron_monto, t):
                val = float(t.replace('.', '').replace(',', '.'))
                montos.insert(0, {"val": val, "idx": i})
                desc_end_idx = i
            else:
                if montos: break
        if not montos: return []
        consumos_detectados = []
        desc_raw = " ".join(tokens[:desc_end_idx])
        vendor_name, cupon, cuotas = self.clean_vendor_details(desc_raw)
        
        # Cupón check
        if cupon == "S/N" and desc_end_idx > 0:
            potential = tokens[desc_end_idx - 1]
            if len(potential) == 6 and potential.isdigit():
                cupon = potential
                vendor_name = vendor_name.replace(potential, "").strip()

        if len(montos) >= 2:
            m_pesos = montos[-2]["val"]
            m_dolares = montos[-1]["val"]
            if m_pesos != 0:
                consumos_detectados.append({"fecha": fecha, "descripcion": vendor_name, "monto": m_pesos, "moneda": "ARS", "banco": banco})
            if m_dolares != 0:
                consumos_detectados.append({"fecha": fecha, "descripcion": vendor_name, "monto": m_dolares, "moneda": "USD", "banco": banco})
        else:
            val = montos[0]["val"]
            moneda = "USD" if "USD" in line.upper() else "ARS"
            consumos_detectados.append({"fecha": fecha, "descripcion": vendor_name, "monto": val, "moneda": moneda, "banco": banco})
        return consumos_detectados

def run_tests():
    ex = MockExtractor()
    samples = [
        ("BBVA Tax", "29-Ene-26 DB IVA $ RESP INSC. 21%                  7.128,10 1.496,90", "29-01-26", "BBVA"),
        ("BBVA Purchase", "16-Ene-26 ADOBE 003198 21.695,30", "16-01-26", "BBVA"),
        ("Galicia USD", "28-12-25 K OPENAI *CHATGPT in1SjRRyCUSD 20,00 188369 20,00", "28-12-25", "GALICIA"),
        ("Galicia ARS", "13-01-26 FEDERACION PAT0000433799978-004-000 58.855,24 009978 58.855,24", "13-01-26", "GALICIA"),
        ("Macro Multi", "29-Ene-26 PERCEP.IVA RG2408 3,0% B.   7128,10 213,84", "29-01-26", "MACRO"),
        ("Payments", "09-Ene-26 SU PAGO EN USD-160,00", "09-01-26", "BBVA")
    ]
    
    for name, line, fecha, banco in samples:
        print(f"\n--- {name} ---")
        print(f"Line: {line}")
        res = ex._parse_columnar_line(line, fecha, banco)
        for r in res:
            print(f"  {r['moneda']} {r['monto']} | {r['descripcion']}")

run_tests()
