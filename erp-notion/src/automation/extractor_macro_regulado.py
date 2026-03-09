import pdfplumber
import easyocr
import re
import json
import os
import sys
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime
from typing import List, Dict, Optional

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class MacroReguladoExtractor:
    """
    Extractor REGULADO para Macro Bank
    Combina procesamiento de imagen avanzado, múltiples pasadas de OCR
    y lógica estricta de extracción de USD para conversión manual.
    """
    
    def __init__(self):
        # Inicializar EasyOCR solo una vez
        self.reader = easyocr.Reader(['es'], gpu=False)
        
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            'ener0': '01', 'dicembre': '12', '8osto': '08', 'agost': '08',
            'diciendre': '12'
        }
        
        self.correcciones = {
            'HRTEL': 'MARTEL', 'HERPAGO': 'MERPAGO', 'ALMAYS': 'ALWAYS', 'alkays': 'ALWAYS',
            'Faceek': 'FACEBOOK', 'ChaTGPT': 'CHATGPT', 'Dicienbre': 'Diciembre',
            'Diciendre': 'Diciembre', 'Enerc': 'Enero'
        }

    def mejorar_imagen(self, pil_img):
        gray = pil_img.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(gray)
        gray = enhancer.enhance(2.0)
        return gray

    def ocr_pagina(self, page_img):
        img_mejorada = self.mejorar_imagen(page_img)
        img_array = np.array(img_mejorada)
        result = self.reader.readtext(img_array, detail=0, paragraph=True)
        return "\n".join(result)

    def limpiar_descripcion(self, desc):
        for mal, bien in self.correcciones.items():
            desc = desc.replace(mal, bien)
        desc = re.sub(r'^\*+\s*', '', desc)
        desc = re.sub(r'\s+\d{6,}\s*$', '', desc)
        return desc.strip()

    def extraer_movimientos(self, texto):
        movements = []
        texto_flujo = texto.replace('\n', ' ')
        # Lista de meses y variaciones OCR para el regex
        meses_regex = "|".join([re.escape(m.capitalize()) for m in self.meses_map.keys()] + [re.escape(m.upper()) for m in self.meses_map.keys()] + [re.escape(m.lower()) for m in self.meses_map.keys()])
        
        # Patrón para detectar inicios de movimientos: 
        # Debe ser DD Mes o Mes AA
        date_pattern = fr'(\d{{1,2}}\s+(?:{meses_regex})|(?:{meses_regex})\s+2[56])'
        fragments = re.split(date_pattern, texto_flujo)
        
        # Siempre abrir en append para debug
        with open("fragments_debug.txt", "a", encoding="utf-8") as f_frag:
            for i in range(1, len(fragments), 2):
                fecha_str_raw = fragments[i].strip()
                bloque = fragments[i+1].strip() if i+1 < len(fragments) else ""
                linea_completa = f"{fecha_str_raw} {bloque}"
                
                f_frag.write(f"\nFRA [{i}]: {linea_completa}\n")
                
                linea_completa = linea_completa.replace(',e8', ',00').replace(',eB', ',00').replace(',e0', ',00').replace(',e ', ',00')
                
                moneda = "ARS"
                if any(x in linea_completa.upper() for x in ["USD", "U$S", "OPENAI", "CHATGPT"]):
                    moneda = "USD"
                
                # Regex robusta para montos con coma decimal
                amounts = re.findall(r'(\d+(?:[.,]\d+)*[.,]\d{2})', linea_completa)
                
                if not amounts:
                    # Fallback para números enteros sin coma (mínimo 4 dígitos)
                    amounts = re.findall(r'(\d{4,9})', linea_completa)
                    if not amounts:
                        f_frag.write("   -> SKIP: No amounts found\n")
                        continue
                
                if moneda == "USD":
                    monto_str = amounts[0].strip()
                else:
                    monto_str = amounts[-1].strip()
                
                try:
                    m_clean = monto_str.replace('.', '').replace(',', '.')
                    m_clean = re.sub(r'[^0-9.]', '', m_clean)
                    if not m_clean: continue
                    
                    if '.' not in m_clean and len(m_clean) >= 4:
                        monto_val = float(m_clean) / 100.0
                    else:
                        monto_val = float(m_clean)
                except ValueError:
                    continue

                dia = "01"
                mes_str = ""
                dm_match = re.match(r'(\d{1,2})\s+([A-Za-z]+)', fecha_str_raw)
                if dm_match:
                    dia, mes_str = dm_match.groups()
                else:
                    ma_match = re.match(r'([A-Za-z]+)\s+2[56]', fecha_str_raw)
                    if ma_match: mes_str = ma_match.group(1)
                
                mes_num = self.meses_map.get(mes_str.lower().strip())
                if not mes_num:
                    f_frag.write(f"   -> SKIP: Month '{mes_str}' unknown\n")
                    continue
                
                dia = dia.zfill(2)
                if dia == "87": dia = "07"
                elif dia == "81": dia = "01"
                
                year = "26" if mes_num != "12" else "25"
                fecha_fmt = f"{dia}-{mes_num}-{year}"
                
                desc_parts = linea_completa.split(monto_str)
                desc_raw = desc_parts[0].replace(fecha_str_raw, "").strip()
                desc_raw = re.sub(r'^\s*(?:\d{2,4}\s+)?(?:\d{6,}\s+)?', '', desc_raw)
                descripcion = self.limpiar_descripcion(desc_raw)
                
                if any(x in descripcion.upper() for x in ["TOTAL CONSUMOS", "PAGO EN PESOS", "SALDO ANTERIOR", "PUNIT", "IVA", "PERCEP", "IIBB", "COMIS", "INTERES", "RESUMEN"]):
                    f_frag.write(f"   -> SKIP: Filtered ({descripcion})\n")
                    continue
                
                if len(descripcion) < 3:
                    f_frag.write(f"   -> SKIP: Desc too short ({descripcion})\n")
                    continue

                f_frag.write(f"   -> FOUND: {fecha_fmt} | {descripcion} | {monto_val}\n")
                print(f"      -> Encontrado: {fecha_fmt} | {descripcion[:30]:<30} | {moneda} {monto_val:>10.2f}")

                movements.append({
                    "fecha": fecha_fmt, "descripcion": descripcion, "monto": monto_val,
                    "moneda": moneda, "banco": "MACRO", "original": linea_completa[:100]
                })

        return movements

    def procesar_pdf(self, pdf_path):
        all_movs = []
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            # Limpiar debug files
            if os.path.exists("ocr_debug_regulated.txt"): os.remove("ocr_debug_regulated.txt")
            if os.path.exists("fragments_debug.txt"): os.remove("fragments_debug.txt")
            
            with open("ocr_debug_regulated.txt", "w", encoding="utf-8") as f_debug:
                for i in range(len(pdf)):
                    page = pdf[i]
                    bitmap = page.render(scale=3)
                    pil_img = bitmap.to_pil()
                    texto = self.ocr_pagina(pil_img)
                    f_debug.write(f"\n--- PAGINA {i+1} ---\n{texto}\n")
                    movs = self.extraer_movimientos(texto)
                    all_movs.extend(movs)
            pdf.close()
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
        return all_movs

def run_regulated_extraction():
    extractor = MacroReguladoExtractor()
    resumen_path = "resumenes/descarga.pdf"
    if not os.path.exists(resumen_path):
        if os.path.exists("resumenes"):
            pdfs = [f for f in os.listdir("resumenes") if f.endswith(".pdf")]
            if pdfs: resumen_path = os.path.join("resumenes", pdfs[0])
            else: return
        else: return

    print("🚀 Iniciando extracción REGULADA de Macro Bank...")
    movements = extractor.procesar_pdf(resumen_path)
    output_path = "macro_consumos_regulado.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(movements, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Extracción completada. {len(movements)} movimientos encontrados.")
    usd_movs = [m for m in movements if m['moneda'] == 'USD']
    if usd_movs:
        print("\n💵 Movimientos en USD:")
        for m in usd_movs: print(f"   -> {m['fecha']} | {m['descripcion']} | USD {m['monto']:.2f}")

if __name__ == "__main__":
    run_regulated_extraction()
