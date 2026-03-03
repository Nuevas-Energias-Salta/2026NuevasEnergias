import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import json
import re
import threading
import requests
from datetime import datetime
import pdfplumber
import pypdfium2 as pdfium
import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# --- CONFIGURACIÓN DE NOTION ---
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
CXP_DB_ID = "2e0c81c3-5804-8123-b1ae-d9b3579e0410"
PROVEEDORES_DB_ID = "2e0c81c3-5804-81e0-94b3-e507ea920f15"
CENTROS_DB_ID = "2e0c81c3-5804-81e7-80a0-dc51608efdd4"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Mapa de meses para BBVA y otros
MESES_MAP_ABR = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
}

class ExtractionEngine:
    def __init__(self):
        self.reader = None # Se carga bajo demanda para no ralentizar inicio
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            'diciendre': '12', '~gosto': '08', 'agosto': '08', 'septiembre': '09'
        }
        self.col_offsets = {"PESOS": -1, "DOLARES": -1} # Inicializar para evitar AttributeError

    def init_ocr(self):
        if self.reader is None:
            self.reader = easyocr.Reader(['es'])

    def corregir_texto(self, texto):
        res = texto.upper()
        res = res.replace('MERPAGO', 'MERCADO PAGO')
        res = res.replace('HLWAYS', 'ALWAYS')
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
        # Buscar 6 dígitos aislados o al inicio
        match_cupon = re.search(r'\b(\d{6})\b', desc)
        if match_cupon:
            cupon = match_cupon.group(1)
            desc = desc.replace(cupon, "").strip()
            
        # 3. Limpiar prefijos de pago (MERPAGO*, etc)
        desc = re.sub(r'^(MERPAGO\*|MP\*|GOOGLE\*|PAYU\*|MERCADO PAGO\*|\*|F |K )', '', desc, flags=re.IGNORECASE).strip()
        
        # 4. Limpiar sufijos de moneda y ruidos/montos residuales
        # Eliminar si termina en algo con formato de monto (ej: 32,00 o USD 32,00 o ARS 1.234,56)
        desc = re.sub(r'\s*(?:USD|ARS|ARS\$|\$)?\s*\d+[\d\.]*,[0-9]{2}$', '', desc, flags=re.IGNORECASE).strip()
        desc = re.sub(r'\s+USD\s*$', '', desc, flags=re.IGNORECASE).strip()
        desc = re.sub(r'in1SoU4VCUSD', '', desc, flags=re.IGNORECASE).strip()
        
        # 5. Limpieza final de asteriscos y espacios
        vendor_name = desc.replace("*", "").strip()
        if not vendor_name: vendor_name = raw_desc
        
        return vendor_name, cupon, cuotas

    def mejorar_imagen(self, pil_img):
        img = pil_img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img

    def _parse_columnar_line(self, line, fecha, banco, titular="GENERAL"):
        """Lógica común para procesar una línea detectando columnas de PESOS y DÓLARES."""
        # Pre-procesar para separar montos pegados (ej: USD-160,00)
        limpio = re.sub(r'([A-Za-z])-?(\d+)', r'\1 \2', line)
        limpio = re.sub(r'([A-Za-z])-(\d+[\.,])', r'\1 -\2', limpio)
        
        tokens = limpio.split()
        if len(tokens) < 2: return []

        # Pre-procesar tokens: Unir números partidos por espacios (ej: "4.  956,34")
        merged_tokens = []
        it_tok = 0
        while it_tok < len(tokens):
            t = tokens[it_tok]
            if t.endswith('.') and it_tok + 1 < len(tokens) and re.match(r'^\d{1,3},\d{2}$', tokens[it_tok+1]):
                merged_tokens.append(t + tokens[it_tok+1])
                it_tok += 2
            else:
                merged_tokens.append(t)
                it_tok += 1
        tokens = merged_tokens
        
        # 1. Identificar montos al final (de dcha a izq)
        montos = []
        desc_end_idx = len(tokens)
        # Patrón más flexible: admite . o , como decimal. Opcional prefijo $.
        patron_monto = r'^-?\$?\d{1,3}(?:\.\d{3})*,\d{2}$|^-?\$?\d+,\d{2}$|^-?\$?\d+\.\d{2}$|^-?\d+$'
        
        for i in range(len(tokens)-1, -1, -1):
            t = tokens[i]
            if re.match(patron_monto, t) and t not in ['/', '//']:
                val = self._parse_monto(t)
                idx_start = line.rfind(t)
                idx_center = idx_start + (len(t) / 2)
                montos.insert(0, {"val": val, "idx": i, "idx_center": idx_center})
                desc_end_idx = i
            elif t.upper() in ["USD", "ARS", "U$S", "DOLARES", "DÓLARES"]:
                desc_end_idx = i
                continue
            else: 
                # Podría ser un cupón o parte de descripción
                break
        
        if not montos: return []
        
        # Anti-Duplicación: Si el penúltimo monto está pegado a un "USD" o "U$S" en la descripción, 
        # o si el primer monto aparece dentro de la descripción, es parte de la descripción.
        if len(montos) >= 2:
            # Caso: ... USD 20,00   20,00
            idx_penult = montos[-2]["idx"]
            if idx_penult > 0:
                prev_t = tokens[idx_penult-1].upper()
                # Si el monto está precedido por USD, es el monto "informativo" de la descripción
                if prev_t in ["USD", "U$S", "DÓLARES", "DOLARES", "US$", "DLS"]:
                    desc_end_idx = montos[-2]["idx"] + 1
                    montos.pop(-2)
            
            # Caso Galicia donde el monto en pesos a veces se repite al final
            # ... 110.888,83   0,00
            if len(montos) >= 2 and montos[-1]["val"] == 0:
                montos.pop(-1)
        
        if not montos: return []
        
        # Casos según cantidad de montos encontrados
        consumos_detectados = []
        
        desc_start_idx = 0
        # Skip date tokens (DD Month [YY] or DD-MM-YY)
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # Simple check for DD Month YY (Macro style)
            if i + 2 < len(tokens) and t.isdigit() and len(t) <= 2:
                next_t = tokens[i+1].lower()
                if next_t in self.meses_map:
                    i += 3 # Skip Day Month Year
                    continue
            # Single token date
            if re.match(r'^\d{1,2}[-/]\d{1,2}([-/]\d{2,4})?$', t):
                i += 1
                continue
            desc_start_idx = i
            break

        desc_raw = " ".join(tokens[desc_start_idx:desc_end_idx])
        if len(desc_raw) < 3: return []
        
        vendor_name, cupon, cuotas = self.clean_vendor_details(desc_raw)

        # Regla de Oro para Impuestos/Cargos: Siempre ARS
        # Buscamos en la línea original para mayor cobertura
        es_impuesto = any(x in line.upper() for x in ["IVA", "SELLOS", "PERCEP", "COMISION", "ADOBE", "INTERES", "PUNIT", "DB.RG"])

        if es_impuesto:
            # Si es impuesto, el segundo monto suele ser el valor del impuesto y el primero la base.
            # Tomamos el último monto disponible.
            val_final = montos[-1]["val"]
            consumos_detectados.append({
                "fecha": fecha, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas,
                "monto": abs(val_final), "moneda": "ARS", "banco": banco, "titular": titular
            })
        elif len(montos) >= 2:
            val1 = montos[0]["val"]
            val2 = montos[1]["val"]
            # Si los montos son idénticos y hay mención de USD, es solo un consumo en dólares
            if abs(val1 - val2) < 0.01 and ("USD" in line.upper() or "U$S" in line.upper()):
                consumos_detectados.append({
                    "fecha": fecha, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas,
                    "monto": abs(val2), "moneda": "USD", "banco": banco, "titular": titular
                })
            else:
                # Consumo dual real o Pesos + Dólar
                consumos_detectados.append({
                    "fecha": fecha, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas,
                    "monto": abs(val1), "moneda": "ARS", "banco": banco, "titular": titular
                })
                consumos_detectados.append({
                    "fecha": fecha, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas,
                    "monto": abs(val2), "moneda": "USD", "banco": banco, "titular": titular
                })
        else:
            val = montos[0]["val"]
            pos_center = montos[0]["idx_center"]
            
            # Moneda por columna
            if hasattr(self, 'col_offsets') and self.col_offsets["PESOS"] != -1 and self.col_offsets["DOLARES"] != -1:
                dist_p = abs(pos_center - self.col_offsets["PESOS"])
                dist_d = abs(pos_center - self.col_offsets["DOLARES"])
                if dist_d < dist_p * 0.5: moneda = "USD"
                elif "USD" in vendor_name.upper() or "USD" in line.upper(): moneda = "USD" if dist_d < dist_p * 1.5 else "ARS"
                else: moneda = "ARS"
            else:
                moneda = "USD" if "USD" in line.upper() else "ARS"

            consumos_detectados.append({
                "fecha": fecha, "descripcion": vendor_name, "cupon": cupon, "cuotas": cuotas,
                "monto": abs(val), "moneda": moneda, "banco": banco, "titular": titular
            })
        
        # Actualizar diagnósticos si estamos en modo manual
        if hasattr(self, 'diagnostics') and titular != "GENERAL" and titular != "PENDING":
            for c in consumos_detectados:
                self.diagnostics[titular]['detectado'][c['moneda']] += c['monto']

        return consumos_detectados

    def extraer_macro_texto(self, texto):
        patron = r'^\s*(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+(\d{2,4}))?\s+(.+)$'
        consumos_totales = []
        items_temp = []
        self.col_offsets = {"PESOS": -1, "DOLARES": -1}
        self.diagnostics = {}

        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            up = line.upper()

            # Detectar cabecera para offsets (PESOS - DOLARES)
            if "PESOS" in up and ("DOLARES" in up or "DÓLARES" in up or "U$S" in up):
                self.col_offsets["PESOS"] = up.find("PESOS")
                self.col_offsets["DOLARES"] = max(up.find("DOLARES"), up.find("DÓLARES"), up.find("U$S"))
                continue

            # Detectar Final de Sección de Titular (Macro: TARJETA XXXX Total Consumos de NAME)
            if "TARJETA" in up and "TOTAL CONSUMOS DE" in up:
                partes = line.split("Consumos de")
                titular_actual = partes[-1].strip()
                # El titular termina donde empiezan los números o el primer asterisco
                titular_actual = re.split(r'[\s\*]{2,}|(?:\d{1,3}(?:\.\d{3})*,\d{2})', titular_actual)[0].strip()
                
                self.diagnostics[titular_actual] = {'detectado': {'ARS': 0, 'USD': 0}, 'esperado': {'ARS': 0, 'USD': 0}}
                
                # Extraer totales esperados
                montos_total = re.findall(r'-?[\d\.]+,[0-9]{2}', line)
                if len(montos_total) >= 1: self.diagnostics[titular_actual]['esperado']['ARS'] = self._parse_monto(montos_total[0])
                if len(montos_total) >= 2: self.diagnostics[titular_actual]['esperado']['USD'] = self._parse_monto(montos_total[1])
                
                # Asignar items acumulados a este titular
                for it in items_temp:
                    it['titular'] = titular_actual
                    if titular_actual in self.diagnostics:
                         self.diagnostics[titular_actual]['detectado'][it['moneda']] += it['monto']
                    consumos_totales.append(it)
                
                items_temp = [] # Reset para el siguiente
                continue

            if any(x in up for x in ["RESUMEN DE", "PAGO MINIMO", "SALDO ACTUAL", "SU PAGO EN", "TOTALES", "PAGO CAJERO"]): continue
            if "SUBTOTAL" in up or "SALDO DE LA" in up or "PROXIMO VENCIM" in up or "SALDO ANTERIOR" in up: continue
            
            # Patrón flexible: DD/MM/YYYY o DD MES [YY]
            patron_v1 = r'^\s*(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{2,4}))?\s+(.+)$'
            patron_v2 = r'^\s*(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+)$'
            
            match1 = re.search(patron_v1, line)
            match2 = re.search(patron_v2, line)
            
            if match1:
                raw_dia = match1.group(1).zfill(2)
                raw_mes = match1.group(2).lower()
                raw_anio = match1.group(3) or datetime.now().strftime("%y")
                mes_num = self.meses_map.get(raw_mes)
                if mes_num:
                    res = self._parse_columnar_line(line, f"{raw_dia}-{mes_num}-{raw_anio}", "MACRO", titular="PENDING")
                    items_temp.extend(res)
            elif match2:
                fecha_norm = match2.group(1).replace('/', '-')
                res = self._parse_columnar_line(line, fecha_norm, "MACRO", titular="PENDING")
                items_temp.extend(res)
        
        # Items finales (impuestos/intereses que no tienen un titular específico al final)
        for it in items_temp:
            it['titular'] = "GENERAL"
            consumos_totales.append(it)
            
        return consumos_totales

    def extraer_gemini_markdown(self, texto, banco="MACRO"):
        """Parsea tablas Markdown o texto plano colapsado generado por Gemini."""
        consumos = []
        self.diagnostics = {"GENERAL": {'detectado': {'ARS': 0, 'USD': 0}, 'esperado': {'ARS': 0, 'USD': 0}}}
        titular_actual = "GENERAL"
        
        # Pre-procesamiento: Inyectar saltos de línea en texto "smashed"
        # Delimitar por fecha (DD-Mon-YY) o por la palabra "Total"
        if len(texto.split('\n')) < 10:
            texto = re.sub(r'(\d{2}-[A-Za-z]{3}-\d{2})', r'\n\1', texto)
            texto = re.sub(r'(Total)', r'\n\1', texto, flags=re.IGNORECASE)

        lineas = texto.split('\n')
        
        # Regex para tablas Markdown (6 columnas)
        re_tabla = r'^\|?\s*([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|?$'
        # Regex para tabla de impuestos (3 columnas)
        re_impuestos = r'^\|?\s*([^|]+)\|([^|]+)\|([^|]+)\|?$'
        # Regex ROBUSTA para texto plano colapsado (FechaComercio...Monto)
        # Formato: DD-Mon-YY Description [Cupon] [Cuotas] ARS [USD]
        re_smashed = r'^(\d{2}-[A-Za-z]{3}-\d{2})\s*(.*?)\s+(-?[\d\.]+,[0-9]{2})(?:\s+(-?[\d\.]+,[0-9]{2}))?$'
        
        for line in lineas:
            line = line.strip()
            if not line or line.startswith('| :') or '| Fecha |' in line: continue
            
            # Detectar Titular (Ej: #### 2. Consumos Gabriel I Ruiz o Consumos: MARCIA M AGUERO)
            if "CONSUMOS" in line.upper() and len(line) < 60:
                header_parts = re.split(r'CONSUMOS', line, flags=re.IGNORECASE)
                if len(header_parts) > 1:
                    titular_actual = header_parts[1].replace(':', '').replace('#', '').strip()
                    if not titular_actual: titular_actual = "GENERAL"
                if titular_actual not in self.diagnostics:
                    self.diagnostics[titular_actual] = {'detectado': {'ARS': 0, 'USD': 0}, 'esperado': {'ARS': 0, 'USD': 0}}

            if line.upper().startswith("TOTAL") and len(line) < 40: 
                # Si es una línea de Total de Gemini, extraemos lo que Gemini CREE que es el total
                montos_total = re.findall(r'-?[\d\.]+,[0-9]{2}', line)
                if montos_total:
                    # En bank summaries, si hay 2 montos en Total, suele ser ARS y USD
                    if len(montos_total) >= 2:
                        self.diagnostics[titular_actual]['esperado']['ARS'] = self._parse_monto(montos_total[-2])
                        self.diagnostics[titular_actual]['esperado']['USD'] = self._parse_monto(montos_total[-1])
                    else:
                        m_val = self._parse_monto(montos_total[0])
                        # Heurística: si es chico, suele ser USD
                        if m_val < 500 and "USD" in line.upper(): # Ajustar según necesidad
                            self.diagnostics[titular_actual]['esperado']['USD'] = m_val
                        else:
                            self.diagnostics[titular_actual]['esperado']['ARS'] = m_val
                continue 
            
            if "FechaComercio" in line: continue # Saltar encabezado pegado
            
            # 1. Intentar Markdown Table
            match = re.match(re_tabla, line)
            if match and '|' in line:
                raw_fecha = match.group(1).strip()
                comercio = match.group(2).strip()
                cupon = match.group(3).strip()
                cuotas = match.group(4).strip()
                m_ars = match.group(5).strip()
                m_usd = match.group(6).strip()
                
                if raw_fecha.lower() == "total" or "total" in raw_fecha.lower(): continue
                fecha_norm = self._normalizar_fecha_gemini(raw_fecha)
                
                try:
                    val_usd = self._parse_monto(m_usd)
                    val_ars = self._parse_monto(m_ars)
                    if val_usd > 0:
                        consumos.append({"fecha": fecha_norm, "descripcion": comercio, "cupon": cupon, "cuotas": cuotas, "monto": abs(val_usd), "moneda": "USD", "banco": banco, "titular": titular_actual})
                        self.diagnostics[titular_actual]['detectado']['USD'] += abs(val_usd)
                    elif val_ars != 0:
                        consumos.append({"fecha": fecha_norm, "descripcion": comercio, "cupon": cupon, "cuotas": cuotas, "monto": abs(val_ars), "moneda": "ARS", "banco": banco, "titular": titular_actual})
                        self.diagnostics[titular_actual]['detectado']['ARS'] += abs(val_ars)
                except: continue
                continue

            # 2. Intentar Texto Plano Smashed (Lo que mandó el usuario ahora)
            # 03-Sep-24 ENERGE S.A. 000070 11/12 274.506,00
            # Buscamos primero la fecha al inicio
            match_smashed = re.search(r'^(\d{2}-[A-Za-z]{3}-\d{2})\s*(.*)$', line)
            if match_smashed:
                fecha_norm = match_smashed.group(1)
                resto = match_smashed.group(2)
                
                # Buscar montos al final del resto
                montos_final = re.findall(r'-?[\d\.]+,[0-9]{2}', resto)
                
                if montos_final:
                    m1 = montos_final[-1]
                    m2 = montos_final[-2] if len(montos_final) >= 2 else None
                    
                    # El resto restante es la descripción + cupón + cuotas
                    desc_completa = resto
                    for m in montos_final:
                        # Reemplazar solo la última ocurrencia del monto para no romper si el monto aparece en la descripción
                        # Pero usualmente los montos están al final.
                        idx = desc_completa.rfind(m)
                        if idx != -1:
                            desc_completa = desc_completa[:idx] + desc_completa[idx+len(m):]
                    
                    desc_completa = desc_completa.strip()
                    
                    # Limpiar palabras basura de la descripción (Total, Subtotal)
                    desc_completa = re.sub(r'\b(TOTAL|TOTALES|SUBTOTAL)\b', '', desc_completa, flags=re.IGNORECASE).strip()
                    
                    # Intentar extraer cuotas y cupón de la descripción restante
                    vendor, cupon, cuotas = self.clean_vendor_details(desc_completa)
                    
                    if m2:
                        val2 = self._parse_monto(m1) # El último suele ser el de la derecha (moneda 2)
                        val1 = self._parse_monto(m2) # El anteúltimo suele ser el de la izquierda (moneda 1)
                        
                        # Heurística mejorada para Macro: si hay 2 montos, el primero es ARS y el segundo USD
                        # A menos que la descripción diga explícitamente algo
                        if "USD" in line.upper() or "U$S" in line.upper(): # Si hay mención explícita
                            consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val1), "moneda": "ARS", "banco": banco, "titular": titular_actual})
                            self.diagnostics[titular_actual]['detectado']['ARS'] += abs(val1)
                            consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val2), "moneda": "USD", "banco": banco, "titular": titular_actual})
                            self.diagnostics[titular_actual]['detectado']['USD'] += abs(val2)
                        else:
                            # Por defecto, si el segundo es mucho más chico, es USD
                            if val2 < (val1 / 10) and val2 != 0:
                                consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val1), "moneda": "ARS", "banco": banco, "titular": titular_actual})
                                self.diagnostics[titular_actual]['detectado']['ARS'] += abs(val1)
                                consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val2), "moneda": "USD", "banco": banco, "titular": titular_actual})
                                self.diagnostics[titular_actual]['detectado']['USD'] += abs(val2)
                            else:
                                # Ambos en ARS? Raro en resúmenes, pero p.ej. si m2 es 0 o similar
                                consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val1), "moneda": "ARS", "banco": banco, "titular": titular_actual})
                                self.diagnostics[titular_actual]['detectado']['ARS'] += abs(val1)
                    else:
                        val = self._parse_monto(m1)
                        moneda = "USD" if "USD" in line.upper() or "U$S" in line.upper() else "ARS"
                        consumos.append({"fecha": fecha_norm, "descripcion": vendor, "cupon": cupon, "cuotas": cuotas, "monto": abs(val), "moneda": moneda, "banco": banco, "titular": titular_actual})
                        self.diagnostics[titular_actual]['detectado'][moneda] += abs(val)
                continue
        
        return consumos

    def _parse_monto(self, text):
        if not text or text in ['-', '', '0,00', '0.00', '0']: return 0
        text = text.replace('$', '').replace(' ', '').strip()
        try:
            if ',' in text and '.' in text: return float(text.replace('.', '').replace(',', '.'))
            if ',' in text: return float(text.replace(',', '.'))
            return float(text)
        except: return 0

    def _normalizar_fecha_gemini(self, text):
        """Convierte '08 Enero' o '08 Enero 26' a DD-MM-YY"""
        text = text.lower().replace('.', '').strip()
        # Caso: 08 enero 26 o 08-01-26
        parts = re.split(r'[-/\s]+', text)
        if len(parts) >= 2:
            d = parts[0].zfill(2)
            m_raw = parts[1]
            m = self.meses_map.get(m_raw, m_raw.zfill(2))
            y = parts[2][-2:] if len(parts) >= 3 else datetime.now().strftime("%y")
            return f"{d}-{m}-{y}"
        return text

    def extraer_galicia_texto(self, texto):
        """Parser específico para texto de resúmenes Galicia.
        
        Formato ARS: DD-MM-YY [FLAG] DESCRIPCION [CUOTAS] CUPON MONTO
        Formato USD: DD-MM-YY [FLAG] DESCRIPCION USD MONTO CUPON MONTO
        """
        consumos = []
        self.diagnostics = {"GENERAL": {'detectado': {'ARS': 0, 'USD': 0}, 'esperado': {'ARS': 0, 'USD': 0}}}
        
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            
            up = line.upper()
            # Saltar encabezados y totales
            if "TOTAL" in up or ("PESOS" in up and "DOLAR" in up): continue
            if "FECHA" in up[:10]: continue
            
            # Matchear fecha al inicio: DD-MM-YY
            match = re.match(r'^(\d{2}-\d{2}-\d{2})\s+(.+)$', line)
            if not match: continue
            
            fecha = match.group(1)
            resto = match.group(2)
            
            # Limpiar flag inicial (K, F, E, * seguido de espacio)
            resto_limpio = re.sub(r'^[KFEC*]\s+', '', resto).strip()
            
            # Determinar si es USD
            es_usd = "USD" in up or "U$S" in up
            
            if es_usd:
                # === LÍNEA USD ===
                # Formato: DESCRIPCION USD MONTO CUPON MONTO
                # Ejemplo: OPENAI *CHATGPT  in1SjRRyCUSD       20,00 188369 20,00
                
                # Buscar "USD" seguido del monto
                usd_match = re.search(r'USD\s+([\d.,]+)', resto_limpio, re.IGNORECASE)
                if not usd_match:
                    usd_match = re.search(r'U\$S\s+([\d.,]+)', resto_limpio, re.IGNORECASE)
                
                if not usd_match: continue
                
                monto = self._parse_monto(usd_match.group(1))
                if monto <= 0: continue
                
                # Descripción: todo antes de USD
                pos_usd = resto_limpio.upper().find("USD")
                if pos_usd == -1: pos_usd = resto_limpio.upper().find("U$S")
                desc_part = resto_limpio[:pos_usd].strip()
                
                # Limpiar basura del final de la descripción (IDs tipo in1SjRRyC)
                desc_part = re.sub(r'\s+[a-zA-Z0-9]{6,}$', '', desc_part).strip()
                
                # Buscar cupón después del monto USD (6 dígitos aislados)
                after_usd = resto_limpio[usd_match.end():]
                cupon_match = re.search(r'\b(\d{6})\b', after_usd)
                cupon = cupon_match.group(1) if cupon_match else "S/N"
                
                # Buscar cuotas en la descripción
                cuotas_match = re.search(r'(\d{2}/\d{2})', desc_part)
                cuotas = cuotas_match.group(1) if cuotas_match else ""
                if cuotas: desc_part = desc_part.replace(cuotas, '').strip()
                
                # Limpiar nombre
                vendor = re.sub(r'\*', ' ', desc_part).strip()
                vendor = re.sub(r'\s+', ' ', vendor).strip()
                if not vendor: vendor = desc_part
                
                consumos.append({
                    "fecha": fecha, "descripcion": vendor, "cupon": cupon,
                    "cuotas": cuotas, "monto": monto,
                    "moneda": "USD", "banco": "GALICIA", "titular": "GENERAL"
                })
                self.diagnostics["GENERAL"]['detectado']['USD'] += monto
                
            else:
                # === LÍNEA ARS ===
                # Formato: DESCRIPCION [CUOTAS] CUPON MONTO
                # Ejemplo: MERPAGO*OVERHARD 09/18 486050 110.888,83
                
                # Buscar el último monto con coma (formato argentino: 110.888,83)
                montos = re.findall(r'[\d.]+,\d{2}', resto_limpio)
                if not montos: continue
                
                monto_str = montos[-1]
                monto = self._parse_monto(monto_str)
                if monto <= 0: continue
                
                # Todo antes del monto es descripción + cupón
                pos_monto = resto_limpio.rfind(monto_str)
                desc_part = resto_limpio[:pos_monto].strip()
                
                # Buscar cupón: últimos 6 dígitos aislados antes del monto
                cupon_match = re.search(r'\b(\d{6})\b\s*$', desc_part)
                cupon = "S/N"
                if cupon_match:
                    cupon = cupon_match.group(1)
                    desc_part = desc_part[:cupon_match.start()].strip()
                
                # Buscar cuotas
                cuotas_match = re.search(r'(\d{2}/\d{2})', desc_part)
                cuotas = cuotas_match.group(1) if cuotas_match else ""
                if cuotas: desc_part = desc_part.replace(cuotas, '').strip()
                
                # Limpiar nombre
                vendor = re.sub(r'\*', ' ', desc_part).strip()
                vendor = re.sub(r'\s+', ' ', vendor).strip()
                if not vendor: vendor = desc_part
                
                consumos.append({
                    "fecha": fecha, "descripcion": vendor, "cupon": cupon,
                    "cuotas": cuotas, "monto": monto,
                    "moneda": "ARS", "banco": "GALICIA", "titular": "GENERAL"
                })
                self.diagnostics["GENERAL"]['detectado']['ARS'] += monto
        
        return consumos

    def extraer_bbva_texto(self, texto):
        patron = r'^\s*(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$'
        consumos = []
        
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            
            if "PESOS" in line.upper() and ("DÓLARES" in line.upper() or "DOLARES" in line.upper()):
                self.col_offsets["PESOS"] = line.upper().find("PESOS")
                self.col_offsets["DOLARES"] = max(line.upper().find("DÓLARES"), line.upper().find("DOLARES"))
                continue

            if "TOTAL" in line.upper() or "FECHA" in line[:10].upper(): continue
            
            match = re.search(patron, line)
            if match:
                dia = match.group(1)
                mes_abr = match.group(2).lower()[:3]
                anio = match.group(3)
                mes_num = self.meses_map.get(mes_abr)
                if not mes_num: continue
                
                res = self._parse_columnar_line(line, f"{dia}-{mes_num}-{anio}", "BBVA")
                consumos.extend(res)
        return consumos

    def extraer_pdf_ocr(self, pdf_path, banco, progress_callback=None):
        """Extrae consumos de un PDF usando OCR para cualquier banco."""
        self.init_ocr()
        self.col_offsets = {"PESOS": -1, "DOLARES": -1} # Reset al inicio del documento
        pdf = pdfium.PdfDocument(pdf_path)
        todos_los_consumos = []
        total_paginas = len(pdf)
        
        for i in range(total_paginas):
            if progress_callback: progress_callback(i + 1, total_paginas)
            page = pdf[i]
            pil_img = page.render(scale=3).to_pil()
            img_mejorada = self.mejorar_imagen(pil_img)
            
            # OCR Detallado para reconstruir líneas por coordenadas
            results = self.reader.readtext(np.array(img_mejorada), detail=1)
            
            # Agrupar por Y (con tolerancia de 15px) y ordenar por X
            lines_data = []
            for (bbox, text, prob) in results:
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                x_start = bbox[0][0]
                lines_data.append({"y": y_center, "x": x_start, "text": text})
            
            lines_data.sort(key=lambda x: (x['y'], x['x']))
            
            final_lines = []
            if lines_data:
                curr_y = lines_data[0]['y']
                curr_line_parts = []
                last_x_end = 0
                
                for item in lines_data:
                    if abs(item['y'] - curr_y) > 15: # Nueva línea
                        final_lines.append("".join(curr_line_parts))
                        curr_y = item['y']
                        curr_line_parts = [item['text']]
                        last_x_end = item['x'] + (len(item['text']) * 8)
                    else:
                        # Simulación de espacios para preservar columnas
                        gap = item['x'] - last_x_end
                        num_spaces = max(1, int(gap / 12)) # 12px por espacio aprox
                        curr_line_parts.append(" " * num_spaces + item['text'])
                        last_x_end = item['x'] + (len(item['text']) * 8)
                final_lines.append("".join(curr_line_parts))
            
            texto = self.corregir_texto("\n".join(final_lines))
            
            # Extraer usando la lógica de texto según el banco
            if banco == "MACRO":
                todos_los_consumos.extend(self.extraer_macro_texto(texto))
            elif banco == "GALICIA":
                todos_los_consumos.extend(self.extraer_galicia_texto(texto))
            elif banco == "BBVA":
                todos_los_consumos.extend(self.extraer_bbva_texto(texto))
        
        pdf.close()
        return self._quitar_duplicados(todos_los_consumos)

    def extraer_imagen_ocr(self, img_path, banco):
        """Extrae consumos de una imagen (JPG/PNG)."""
        self.init_ocr()
        pil_img = Image.open(img_path)
        img_mejorada = self.mejorar_imagen(pil_img)
        result = self.reader.readtext(np.array(img_mejorada), detail=0, paragraph=True)
        texto = self.corregir_texto("\n".join(result))
        
        consumos = []
        if banco == "MACRO": consumos = self.extraer_macro_texto(texto)
        elif banco == "GALICIA": consumos = self.extraer_galicia_texto(texto)
        elif banco == "BBVA": consumos = self.extraer_bbva_texto(texto)
        
        return self._quitar_duplicados(consumos)

    def _quitar_duplicados(self, consumos):
        vistos = set()
        unicos = []
        for c in consumos:
            key = (c['fecha'], c['descripcion'], c['monto'], c['moneda'])
            if key not in vistos:
                unicos.append(c)
                vistos.add(key)
        return unicos

    def extraer_bbva(self, pdf_path):
        movements = []
        months_bbva = {"Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04", "May": "05", "Jun": "06", 
                       "Jul": "07", "Ago": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"}
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                for line in text.split('\n'):
                    match = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{2})\s+(.+)$', line)
                    if match:
                        dd, mm_str, yy = match.group(1), match.group(2), match.group(3)
                        mm = months_bbva.get(mm_str.title(), "00")
                        resto = match.group(4)
                        tokens = resto.split()
                        monto = None
                        for t in reversed(tokens):
                            if ',' in t and re.match(r'^-?[\d.]+,[\d]{2}$', t):
                                monto = abs(float(t.replace('.', '').replace(',', '.')))
                                break
                        if monto:
                            desc = " ".join([t for t in tokens if not re.match(r'^-?[\d.]+,[\d]{2}$', t) and len(t) < 10]).strip()
                            movements.append({
                                "fecha": f"{dd}-{mm}-{yy}",
                                "descripcion": desc,
                                "monto": monto,
                                "moneda": "ARS",
                                "banco": "BBVA"
                            })
        return movements

    def extraer_galicia(self, pdf_path):
        movements = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                for line in text.split('\n'):
                    match = re.match(r'^(\d{2}-\d{2}-\d{2})\s+(.+)$', line)
                    if match:
                        fecha, resto = match.group(1), match.group(2)
                        tokens = resto.split()
                        monto = None
                        for t in reversed(tokens):
                            if ',' in t and re.match(r'^-?[\d.]+,[\d]{2}$', t):
                                monto = abs(float(t.replace('.', '').replace(',', '.')))
                                break
                        if monto:
                            desc = " ".join([t for t in tokens if not re.match(r'^-?[\d.]+,[\d]{2}$', t) and len(t) < 10]).strip()
                            movements.append({
                                "fecha": fecha,
                                "descripcion": desc,
                                "monto": monto,
                                "moneda": "ARS",
                                "banco": "GALICIA"
                            })
        return movements

class NotionUploader:
    def __init__(self):
        self.cache = {}

    def get_or_create_vendor(self, name):
        name = name.strip() or "Desconocido"
        if name in self.cache: return self.cache[name]
        try:
            payload = {"filter": {"property": "Nombre", "title": {"equals": name}}}
            res = requests.post(f"https://api.notion.com/v1/databases/{PROVEEDORES_DB_ID}/query", headers=HEADERS, json=payload)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    self.cache[name] = results[0]["id"]
                    return self.cache[name]
            
            payload_create = {
                "parent": {"database_id": PROVEEDORES_DB_ID}, 
                "properties": {"Nombre": {"title": [{"text": {"content": name}}]}, "Categoría": {"multi_select": [{"name": "Otros"}]}}
            }
            res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload_create)
            if res.status_code == 200:
                self.cache[name] = res.json()["id"]
                return self.cache[name]
        except: pass
        return None

    def upload(self, item, callback_status=None):
        try:
            # Usar el nombre limpio para el proveedor
            vendor_id = self.get_or_create_vendor(item['descripcion'])
            
            # Fecha ISO
            # Galicia ya viene como DD-MM-YY, Macro viene como DD-MM-YY o DD-MM-YYYY
            fecha_raw = item['fecha']
            try:
                # Intentar parsear con guiones
                parts = fecha_raw.split('-')
                d, m, y = parts[0], parts[1], parts[2]
                if len(y) == 2: y = f"20{y}"
                fecha_iso = f"{y}-{m}-{d}"
            except:
                fecha_iso = datetime.now().strftime("%Y-%m-%d")
            
            # Título: Ahora es el cupón o cuotas
            factura_n = item['cupon']
            if item['cuotas']:
                factura_n += f" ({item['cuotas']})"

            # Mapeo de Método de Pago por Banco
            banco = item.get('banco', 'MACRO').upper()
            # GEMINI es solo el método de extracción, no un banco real
            if banco == "GEMINI": banco = "MACRO"
            metodo_pago_map = {
                "MACRO": "T VISA MACRO",
                "GALICIA": "T VISA GALICIA",
                "BBVA": "T VISA BBVA"
            }
            metodo_nombre = metodo_pago_map.get(banco, "T VISA MACRO")

            # Preparar montos según moneda (Columna dual en DB)
            monto_props = {}
            if item.get('moneda') == 'USD':
                monto_props["Monto Dolares"] = {"number": item['monto']}
                monto_props["Monto"] = {"number": 0}
            else:
                monto_props["Monto"] = {"number": item['monto']}

            props = {
                "Factura n°": {"title": [{"text": {"content": factura_n}}]},
                "Fecha Factura": {"date": {"start": fecha_iso}},
                "Estado": {"select": {"name": "Pendiente"}},
                "Concepto": {"select": {"name": "Tarjeta de Crédito"}},
                "Categoría": {"select": {"name": "Servicios"}},
                "Método Pago": {"multi_select": [{"name": metodo_nombre}]},
                **monto_props
            }
            if vendor_id: props["Proveedor"] = {"relation": [{"id": vendor_id}]}
            
            payload = {"parent": {"database_id": CXP_DB_ID}, "properties": props}
            res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
            
            if res.status_code != 200:
                print(f"Error Notion: {res.text}")
                return False, res.text
            return True, "OK"
        except Exception as e:
            return False, str(e)

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargador Universal de Resúmenes -> Notion (OCR Integrado)")
        self.root.geometry("900x850")
        self.engine = ExtractionEngine()
        self.uploader = NotionUploader()
        self.items = []
        self._setup_ui()

    def _setup_ui(self):
        # Estilo
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        
        # Botones de Acción (Fijados al fondo)
        bottom_frame = ttk.Frame(self.root, padding="20")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.btn_subir = ttk.Button(bottom_frame, text="SUBIR A NOTION 📤", command=self.subir_notion, state=tk.DISABLED)
        self.btn_subir.pack(side=tk.RIGHT, padx=5)
        
        self.lbl_status = ttk.Label(bottom_frame, text="Listo.")
        self.lbl_status.pack(side=tk.LEFT)

        # Contenedor Principal (Expandible)
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="🚀 Cargador de Consumos", style="Header.TLabel").pack(pady=10)

        # Selector de Banco y Método
        top_controls = ttk.Frame(main_frame)
        top_controls.pack(fill=tk.X, pady=10)

        ttk.Label(top_controls, text="Banco:").grid(row=0, column=0, padx=5)
        self.banco_var = tk.StringVar(value="MACRO")
        ttk.Combobox(top_controls, textvariable=self.banco_var, values=["MACRO", "BBVA", "GALICIA"], width=15).grid(row=0, column=1, padx=5)

        self.usd_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_controls, text="Solo Dólares", variable=self.usd_only_var, command=self.actualizar_tabla).grid(row=0, column=2, padx=10)

        ttk.Button(top_controls, text="Seleccionar Archivo (OCR)", command=self.cargar_archivo).grid(row=0, column=3, padx=10)
        
        self.progress = ttk.Progressbar(top_controls, orient=tk.HORIZONTAL, length=120, mode='determinate')
        self.progress.grid(row=0, column=4, padx=10)
        
        # Area de texto para manual
        ttk.Label(main_frame, text="O pega el texto aquí:").pack(anchor=tk.W, pady=(5, 0))
        self.text_area = scrolledtext.ScrolledText(main_frame, height=6, font=("Consolas", 10))
        self.text_area.pack(fill=tk.X, pady=5)
        
        btn_manual_frame = ttk.Frame(main_frame)
        btn_manual_frame.pack(fill=tk.X)
        ttk.Button(btn_manual_frame, text="Procesar Texto Pegado", command=self.procesar_texto).pack(side=tk.LEFT, padx=5)

        # Tabla de Vista Previa con Scrollbar
        ttk.Label(main_frame, text="Vista Previa de Consumos:").pack(anchor=tk.W, pady=(10, 5))
        
        tree_container = ttk.Frame(main_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_container, columns=("Fecha", "Cupón", "Detalle", "Monto", "Moneda", "Banco"), show="headings", height=10)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Cupón", text="Cupón/Cuotas")
        self.tree.heading("Detalle", text="Detalle")
        self.tree.heading("Monto", text="Monto")
        self.tree.heading("Moneda", text="Mon")
        self.tree.heading("Banco", text="Banco")
        self.tree.column("Fecha", width=80)
        self.tree.column("Cupón", width=120)
        self.tree.column("Detalle", width=300)
        self.tree.column("Monto", width=100, anchor=tk.E)
        self.tree.column("Moneda", width=50)
        self.tree.column("Banco", width=80)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Panel de Diagnóstico
        self.diag_frame = ttk.LabelFrame(main_frame, text="🔍 Diagnóstico de Integridad (por Resumen)")
        self.diag_frame.pack(fill=tk.X, pady=10)
        
        self.diag_text = tk.Text(self.diag_frame, height=4, font=("Consolas", 9), bg="#f0f0f0")
        self.diag_text.pack(fill=tk.X, padx=5, pady=5)

    def status(self, msg):
        self.lbl_status.config(text=msg)
        self.root.update_idletasks()

    def cargar_archivo(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos admitidos", "*.pdf *.png *.jpg *.jpeg *.bmp")])
        if not path: return
        
        self.status("Procesando archivo con OCR...")
        self.progress['value'] = 0
        banco = self.banco_var.get()
        
        def task():
            try:
                def update_prog(curr, total):
                    val = (curr / total) * 100
                    self.root.after(0, lambda: self.progress.config(value=val))

                if path.lower().endswith('.pdf'):
                    self.items = self.engine.extraer_pdf_ocr(path, banco, progress_callback=update_prog)
                else:
                    self.items = self.engine.extraer_imagen_ocr(path, banco)
                
                self.root.after(0, self.actualizar_tabla)
                self.root.after(0, lambda: self.status(f"OCR Finalizado: {len(self.items)} items."))
                self.progress['value'] = 100
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error OCR", str(e)))
                self.root.after(0, lambda: self.status("Error en OCR."))

        threading.Thread(target=task).start()

    def procesar_texto(self):
        texto = self.text_area.get("1.0", tk.END)
        if not texto.strip(): return
        
        # Reset para extracción manual
        self.engine.col_offsets = {"PESOS": -1, "DOLARES": -1}
        
        banco = self.banco_var.get()
        
        if banco == "MACRO":
            self.items = self.engine.extraer_macro_texto(texto)
        elif banco == "GALICIA":
            self.items = self.engine.extraer_galicia_texto(texto)
        elif banco == "BBVA":
            self.items = self.engine.extraer_bbva_texto(texto)

        self.actualizar_tabla()
        self.status(f"Procesados {len(self.items)} movimientos.")
    
    def _procesar_formato_tabs(self, texto):
        """Procesa texto en formato tab-separated (como el que exporta Gems)"""
        consumos = []
        self.engine.diagnostics = {}
        
        for line in texto.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Formato: Fecha | Comercio | Cuota | Importe ARS | Importe USD | Sección | Titular
            parts = line.split('\t')
            
            if len(parts) < 5:
                continue
            
            try:
                fecha = parts[0].strip()
                comercio = parts[1].strip()
                cuota = parts[2].strip() if len(parts) > 2 else ""
                
                # Parsear montos
                monto_ars = 0
                monto_usd = 0
                
                if len(parts) > 3 and parts[3].strip():
                    try:
                        monto_ars = float(parts[3].strip().replace('.', '').replace(',', '.'))
                    except:
                        pass
                
                if len(parts) > 4 and parts[4].strip():
                    try:
                        monto_usd = float(parts[4].strip().replace('.', '').replace(',', '.'))
                    except:
                        pass
                
                seccion = parts[5].strip() if len(parts) > 5 else "Consumos"
                titular = parts[6].strip() if len(parts) > 6 else "GENERAL"
                
                # Determinar tipo y moneda
                if seccion.upper().find("PAGO") >= 0 or "ABONO" in seccion.upper():
                    tipo = "pago"
                    moneda = "ARS"
                elif "IMPUESTO" in seccion.upper() or "CARGO" in seccion.upper():
                    tipo = "impuesto"
                    moneda = "ARS"
                else:
                    tipo = "compra"
                    moneda = "USD" if monto_usd > 0 else "ARS"
                
                monto = monto_ars if monto_ars > 0 else monto_usd
                
                # Agregar a diagnostics
                if titular not in self.engine.diagnostics:
                    self.engine.diagnostics[titular] = {'detectado': {'ARS': 0, 'USD': 0}, 'esperado': {'ARS': 0, 'USD': 0}}
                
                if monto > 0:
                    consumos.append({
                        "fecha": fecha,
                        "descripcion": comercio,
                        "cupon": "",
                        "cuotas": cuota,
                        "monto": monto,
                        "moneda": moneda,
                        "banco": "MACRO",
                        "titular": titular
                    })
                    self.engine.diagnostics[titular]['detectado'][moneda] += monto
                    
            except Exception as e:
                continue
        
        return consumos

    # Función deshabilitada - usar procesar_texto() en su lugar
    # def procesar_gemini(self):
    #     texto = self.text_area.get("1.0", tk.END)
    #     if not texto.strip(): 
    #         messagebox.showwarning("Aviso", "Primero pega el resultado de Gemini en el cuadro de texto superior.")
    #         return
    #     
    #     self.items = self.engine.extraer_gemini_markdown(texto)
    #     self.actualizar_tabla()
    #     if self.items:
    #         self.status(f"Importados {len(self.items)} movimientos desde Gemini.")
    #     else:
    #         messagebox.showinfo("Aviso", "No se encontraron tablas Markdown válidas con el formato esperado.")

    def actualizar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        filtered_items = self.items
        if self.usd_only_var.get():
            filtered_items = [it for it in self.items if it['moneda'] == "USD"]

        for item in filtered_items:
            cupon_display = item['cupon']
            if item['cuotas']: cupon_display += f" ({item['cuotas']})"
            self.tree.insert("", tk.END, values=(item['fecha'], cupon_display, item['descripcion'], f"{item['monto']:,.2f}", item['moneda'], item['banco']))
        
        # Actualizar Panel de Diagnóstico
        self.diag_text.config(state=tk.NORMAL)
        self.diag_text.delete("1.0", tk.END)
        
        if hasattr(self.engine, 'diagnostics') and self.engine.diagnostics:
            for titular, info in self.engine.diagnostics.items():
                det_ars = info['detectado']['ARS']
                esp_ars = info['esperado']['ARS']
                det_usd = info['detectado']['USD']
                esp_usd = info['esperado']['USD']
                
                header = f"Titular: {titular}\n"
                res_ars = f"  ARS: Detectado {det_ars:,.2f} | Esperado {esp_ars:,.2f} -> "
                res_ars += "✅ OK" if abs(det_ars - esp_ars) < 0.1 else "❌ DISCREPANCIA"
                
                line_usd = ""
                if esp_usd > 0 or det_usd > 0:
                    line_usd = f"\n  USD: Detectado {det_usd:,.2f} | Esperado {esp_usd:,.2f} -> "
                    line_usd += "✅ OK" if abs(det_usd - esp_usd) < 0.1 else "❌ DISCREPANCIA"
                
                self.diag_text.insert(tk.END, header + res_ars + line_usd + "\n" + "-"*50 + "\n")
        else:
            self.diag_text.insert(tk.END, "Sin datos de diagnóstico disponibles.")
        
        self.diag_text.config(state=tk.DISABLED)

        if filtered_items:
            self.btn_subir.config(state=tk.NORMAL)
            self.status(f"Se muestran {len(filtered_items)} consumos.")
        else:
            self.btn_subir.config(state=tk.DISABLED)
            self.status("No se detectaron consumos.")

    def subir_notion(self):
        if not messagebox.askyesno("Confirmar", f"¿Subir {len(self.items)} consumos a Notion?"):
            return
        
        self.btn_subir.config(state=tk.DISABLED)
        
        def task():
            exitos = 0
            for i, item in enumerate(self.items):
                self.root.after(0, lambda x=i: self.status(f"Subiendo {x+1}/{len(self.items)}..."))
                ok, error_msg = self.uploader.upload(item)
                if ok:
                    exitos += 1
                else:
                    self.root.after(0, lambda m=error_msg: self.status(f"Fallo en item {i+1}: {m}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Proceso Finalizado", f"Se subieron {exitos} de {len(self.items)} movimientos correctamente."))
            self.root.after(0, lambda: self.status("Proceso finalizado."))

        threading.Thread(target=task).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()

