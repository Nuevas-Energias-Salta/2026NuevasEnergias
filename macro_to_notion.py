import os
import sys
import re
import json
import requests
import io
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pypdfium2 as pdfium
import easyocr
from PIL import Image, ImageEnhance

# Asegurar codificación UTF-8 para la terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de Notion (Extraída de upload_to_notion.py)
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"
PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

class MacroToNotion:
    def __init__(self, gpu=False):
        print("Iniciando Extractor Macro -> Notion...")
        self.reader = easyocr.Reader(['es'], gpu=gpu)
        self.vendor_cache = {}
        
        # Mapeo de meses ruidosos de OCR
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            'diciendre': '12', '~gosto': '08', 'agosto': '08', 'septiembre': '09'
        }

    def mejorar_imagen(self, pil_image):
        """Mejora la imagen para OCR óptimo"""
        gray = pil_image.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        contrast = enhancer.enhance(2.0)
        return contrast

    def corregir_texto(self, texto):
        """Correcciones específicas de OCR para Macro"""
        res = texto.replace('HERPAGO', 'MERPAGO')
        res = res.replace('MerpaGo', 'MERPAGO')
        res = res.replace('ALMAYS', 'ALWAYS')
        res = res.replace('ALMAY', 'ALWAYS')
        res = res.replace('Gridos', 'CHICO')
        res = res.replace('Sanlo', 'SAN LO')
        res = res.replace('HRTEL', 'MARTEL')
        return res

    def clean_vendor_details(self, raw_desc):
        """Separa el nombre del proveedor del cupón y las cuotas."""
        desc = raw_desc.strip()
        
        # 1. Extraer cuotas (ej: C.01/06)
        cuotas = ""
        match_cuotas = re.search(r'(C\.\d{2}/\d{2})', desc)
        if match_cuotas:
            cuotas = match_cuotas.group(1)
            desc = desc.replace(cuotas, "").strip()
            
        # 2. Extraer cupón (6 dígitos usualmente)
        cupon = "S/N"
        match_cupon = re.search(r'\b(\d{6})\b', desc)
        if match_cupon:
            cupon = match_cupon.group(1)
            desc = desc.replace(cupon, "").strip()
            
        # 3. Limpiar prefijos de pago
        desc = re.sub(r'^(MERPAGO\*|MP\*|GOOGLE\*|PAYU\*|MERCADO PAGO\*|\*|F |K )', '', desc, flags=re.IGNORECASE).strip()
        
        # 4. Limpiar sufijos de moneda y montos residuales
        desc = re.sub(r'\s*(?:USD|ARS|ARS\$|\$)?\s*\d+[\d\.]*,[0-9]{2}$', '', desc, flags=re.IGNORECASE).strip()
        desc = re.sub(r'\s+USD\s*$', '', desc, flags=re.IGNORECASE).strip()
        
        # 4. Limpieza final
        vendor_name = desc.replace("*", "").strip()
        if not vendor_name: vendor_name = raw_desc
        
        return vendor_name, cupon, cuotas

    def extraer_desde_texto(self, texto):
        """Lógica de extracción mejorada para texto pegado o extraído."""
        # Detectar banco si es posible, o usar Macro por defecto
        banco = "MACRO"
        if "GALICIA" in texto.upper(): banco = "GALICIA"
        if "BBVA" in texto.upper(): banco = "BBVA"

        consumos = []
        col_offsets = {"PESOS": -1, "DOLARES": -1}
        
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            
            # Detectar cabecera para fijar offsets
            if "PESOS" in line.upper() and ("DÓLARES" in line.upper() or "DOLARES" in line.upper()):
                col_offsets["PESOS"] = line.upper().find("PESOS")
                col_offsets["DOLARES"] = max(line.upper().find("DÓLARES"), line.upper().find("DOLARES"))
                continue

            if "TOTAL" in line.upper(): continue
            
            # Formatos de fecha soportados
            patron_fecha = r'^(\d{1,2})[-/\s]([A-Za-z]{3}|\d{1,2})[-/\s]?(\d{2,4})?\s+(.+)$'
            match = re.search(patron_fecha, line)
            if match:
                f_dia = match.group(1).zfill(2)
                f_mes_raw = match.group(2).lower()
                f_anio = match.group(3) or datetime.now().strftime("%y")
                mes_num = self.meses_map.get(f_mes_raw, f_mes_raw.zfill(2))
                fecha_final = f"{f_dia}-{mes_num}-{f_anio}"
                
                # Tokenización Universal
                limpio = re.sub(r'([A-Za-z])-?(\d+)', r'\1 \2', line)
                limpio = re.sub(r'([A-Za-z])-(\d+[\.,])', r'\1 -\2', limpio)
                tokens = limpio.split()
                
                montos = []
                desc_end_idx = len(tokens)
                patron_monto = r'^-?[\d\.]+,[0-9]{2}$'
                for i in range(len(tokens)-1, -1, -1):
                    t = tokens[i]
                    if re.match(patron_monto, t):
                        val = float(t.replace('.', '').replace(',', '.'))
                        # Guardar posición original en el string
                        idx_start = line.rfind(t)
                        montos.insert(0, {"val": val, "idx": i, "idx_start": idx_start})
                        desc_end_idx = i
                    elif montos: break
                
                if not montos: continue
                
                desc_start_idx = 0
                for i in range(len(tokens)):
                    if not re.search(r'^\d', tokens[i]):
                        desc_start_idx = i
                        break
                
                desc_raw = " ".join(tokens[desc_start_idx:desc_end_idx])
                vendor_name, cupon, cuotas = self.clean_vendor_details(desc_raw)
                
                if len(montos) >= 2:
                    m_p = montos[-2]["val"]; m_d = montos[-1]["val"]
                    if m_p != 0: consumos.append({"fecha": fecha_final, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas, "monto": m_p, "moneda": "ARS", "original": line, "banco": banco})
                    if m_d != 0: consumos.append({"fecha": fecha_final, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas, "monto": m_d, "moneda": "USD", "original": line, "banco": banco})
                else:
                    # Un solo monto: Usar Offsets o fallback
                    val = montos[0]["val"]
                    pos_monto = montos[0]["idx_start"]
                    
                    if col_offsets["PESOS"] != -1 and col_offsets["DOLARES"] != -1:
                        mid = (col_offsets["PESOS"] + col_offsets["DOLARES"]) / 2
                        moneda = "USD" if pos_monto > mid else "ARS"
                    else:
                        moneda = "USD" if "USD" in line.upper() else "ARS"
                    
                    consumos.append({"fecha": fecha_final, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas, "monto": val, "moneda": moneda, "original": line, "banco": banco})
        return consumos

    def extraer_consumos(self, pdf_path):
        """Extrae consumos del PDF usando OCR"""
        print(f"📄 Procesando PDF: {pdf_path}")
        pdf = pdfium.PdfDocument(pdf_path)
        todos_los_consumos = []
        
        for i in range(len(pdf)):
            print(f"   Página {i+1}...")
            page = pdf[i]
            pil_img = page.render(scale=3).to_pil()
            img_mejorada = self.mejorar_imagen(pil_img)
            
            # OCR
            result = self.reader.readtext(np.array(img_mejorada), detail=0, paragraph=True)
            texto = self.corregir_texto("\n".join(result))
            
            # Extraer usando la lógica común
            todos_los_consumos.extend(self.extraer_desde_texto(texto))
        
        pdf.close()
        # Eliminar duplicados exactos
        vistos = set()
        unicos = []
        for c in todos_los_consumos:
            key = (c['fecha'], c['descripcion'], c['monto'])
            if key not in vistos:
                unicos.append(c)
                vistos.add(key)
        
        return unicos

    def get_or_create_vendor(self, name):
        """Busca o crea proveedor en Notion"""
        name = name.strip() or "Desconocido"
        if name in self.vendor_cache: return self.vendor_cache[name]
        
        # Buscar
        payload = {"filter": {"property": "Nombre", "title": {"equals": name}}}
        res = requests.post(f"https://api.notion.com/v1/databases/{PROVEEDORES_DB_ID}/query", headers=HEADERS, json=payload)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                vid = results[0]["id"]
                self.vendor_cache[name] = vid
                return vid
                
        # Crear
        print(f"   Creando proveedor: {name}")
        payload_create = {
            "parent": {"database_id": PROVEEDORES_DB_ID},
            "properties": {"Nombre": {"title": [{"text": {"content": name}}]}, "Categoría": {"multi_select": [{"name": "Otros"}]}}
        }
        res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload_create)
        if res.status_code == 200:
            vid = res.json()["id"]
            self.vendor_cache[name] = vid
            return vid
        return None

    def subir_a_notion(self, consumos):
        """Sube la lista de consumos a Notion"""
        print(f"⬆️ Subiendo {len(consumos)} consumos a Notion...")
        exitos = 0
        
        for i, c in enumerate(consumos):
            # Limpiar nombre para proveedor
            vendor_name = re.sub(r'^(MERPAGO\*|MP\*|GOOGLE\*|PAYU\*)', '', c['descripcion'], flags=re.IGNORECASE).strip()
            if not vendor_name: vendor_name = c['descripcion']
            
            vendor_id = self.get_or_create_vendor(vendor_name)
            
            # Fecha ISO
            try:
                dt = datetime.strptime(c['fecha'], "%d-%m-%y")
                fecha_iso = dt.strftime("%Y-%m-%d")
            except:
                fecha_iso = datetime.now().strftime("%Y-%m-%d")

            # Título (Factura n°)
            factura_n = c.get('cupon', 'S/N')
            if c.get('cuotas'):
                factura_n += f" ({c['cuotas']})"

            # Mapeo de Método de Pago por Banco
            # Intentar deducir banco desde la descripción o usar Macro por defecto para este script
            banco = c.get('banco', 'MACRO').upper()
            if "GALICIA" in c.get('original', '').upper(): banco = "GALICIA"
            if "BBVA" in c.get('original', '').upper(): banco = "BBVA"

            metodo_pago_map = {
                "MACRO": "Visa Macro",
                "GALICIA": "Visa Galicia",
                "BBVA": "Visa BBVA"
            }
            metodo_nombre = metodo_pago_map.get(banco, "Visa Macro")

            props = {
                "Factura n°": {"title": [{"text": {"content": factura_n}}]},
                "Monto": {"number": c['monto']},
                "Fecha Factura": {"date": {"start": fecha_iso}},
                "Estado": {"select": {"name": "Pendiente"}},
                "Concepto": {"select": {"name": "Tarjeta de Crédito"}},
                "Categoría": {"select": {"name": "Servicios"}},
                "Método Pago": {"multi_select": [{"name": metodo_nombre}]}
            }
            if vendor_id: props["Proveedor"] = {"relation": [{"id": vendor_id}]}

            payload = {"parent": {"database_id": CXP_DB_ID}, "properties": props}
            res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
            
            if res.status_code == 200:
                print(f"   [{i+1}/{len(consumos)}] ✅ {vendor_name} - ${c['monto']}")
                exitos += 1
            else:
                print(f"   [{i+1}/{len(consumos)}] ❌ Error {vendor_name}: {res.text}")
                
        return exitos

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Macro To Notion OCR / Text')
    parser.add_argument('--pdf', help='Ruta al PDF de Macro')
    parser.add_argument('--txt', help='Ruta al archivo de TEXTO de Macro')
    parser.add_argument('--dry-run', action='store_true', help='Solo extraer, no subir')
    args = parser.parse_args()

    runtime = MacroToNotion()
    consumos = []

    if args.txt:
        print(f"📖 Leyendo texto desde: {args.txt}")
        with open(args.txt, 'r', encoding='utf-8') as f:
            texto = f.read()
        consumos = runtime.extraer_desde_texto(texto)
    elif args.pdf:
        consumos = runtime.extraer_consumos(args.pdf)
    else:
        # Intento por defecto con PDF si existe
        default_pdf = 'resumenes/descarga.pdf'
        if os.path.exists(default_pdf):
            consumos = runtime.extraer_consumos(default_pdf)
        else:
            print("❌ Error: Debes especificar --pdf o --txt")
            return
    
    if not consumos:
        print("❌ No se encontraron consumos.")
        return

    print(f"📊 Se encontraron {len(consumos)} consumos.")
    
    if args.dry_run:
        print("🚦 Modo DRY-RUN activo. Mostrando resultados:")
        for i, c in enumerate(consumos, 1):
            print(f"   {i:2}. {c['fecha']} | {c['moneda']} {c['monto']} | {c['descripcion']}")
    else:
        exitos = runtime.subir_a_notion(consumos)
        print(f"\nTRABAJO FINALIZADO: {exitos}/{len(consumos)} subidos con éxito.")

if __name__ == "__main__":
    main()

