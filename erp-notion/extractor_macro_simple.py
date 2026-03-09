import pdfplumber
import easyocr
import re
import json
import os
from datetime import datetime
from typing import List, Dict
import numpy as np

class MacroOCR_simple:
    """Extractor OCR simple para Macro Bank sin caracteres problemáticos"""
    
    def __init__(self):
        print("Extractor Macro OCR iniciado")
        
        # Mapeo de meses
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            'oct': '10', 'dic': '12'
        }
        
        # Correcciones de OCR
        self.correcciones = {
            'HRTEL': 'MARTEL', 'HARTEL': 'MARTEL',
            'MERPAGO': 'MERPAGO', 'MerpaGo': 'MERPAGO', 'Merpago': 'MERPAGO',
            'ALMAYS': 'ALWAYS', 'ALMAY': 'ALWAYS', 'ALWAYS': 'ALWAYS',
            'ALKAYS': 'ALWAYS', 'alkays': 'ALWAYS',
            'Sanlo': 'SAN LO', 'San Lo': 'SAN LO',
            'Chico': 'CHICO', 'CHICO': 'CHICO',
            'Faceek': 'FACEBOOK', 'FacEBOOK': 'FACEBOOK',
            'OPENAI': 'OPENAI',
            'LactEA': 'LATAM', 'LATAM': 'LATAM',
            'Gridos': 'CHICO', 'GRIDOS': 'CHICO',
            'ChaTGPT': 'CHATGPT', 'CHATGPT': 'CHATGPT',
            '49262,01': '49282,01',  # PINTURERIAS MARTEL
        }
    
    def corregir_texto(self, texto):
        """Aplica correcciones de OCR"""
        texto_corregido = texto
        
        for error, correccion in self.correcciones.items():
            texto_corregido = texto_corregido.replace(error, correccion)
        
        return texto_corregido
    
    def extraer_consumos(self, texto):
        """Extrae consumos del texto OCR"""
        
        # Buscar "SU PAGO EN PESOS"
        pago_match = re.search(r'SU PAGO EN PESOS', texto.upper())
        if not pago_match:
            return []
        
        texto_despues_pago = texto[pago_match.end():]
        
        # Patrón para consumos
        patron = r'(\d{1,2})\s+([A-Za-z]+)\s+([^0-9]*?)(\d+[.,]\d{2})'
        
        matches = list(re.finditer(patron, texto_despues_pago))
        consumos = []
        
        for match in matches:
            try:
                day = match.group(1).strip()
                month = match.group(2).lower().strip()
                desc_part = match.group(3).strip()
                amount = match.group(4)
                
                # Normalizar mes
                month_num = self.meses_map.get(month)
                if not month_num:
                    continue
                
                # Formatear día y año
                day = f"0{day}" if len(day) == 1 else day
                year = "25" if month_num == "12" else "26"
                fecha = f"{day}-{month_num}-{year}"
                
                # Convertir monto
                try:
                    monto = float(amount.replace('.', '').replace(',', '.'))
                except:
                    continue
                
                # Extraer descripción limpia
                amount_in_desc = re.search(r'(\d+[.,]\d{2})$', desc_part)
                if amount_in_desc:
                    desc = desc_part[:amount_in_desc.start()].strip()
                else:
                    desc = desc_part.strip()
                
                # Aplicar correcciones
                desc = self.corregir_texto(f"MERPAGO*{desc}")
                
                # Quitar caracteres raros
                desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()
                
                # Determinar moneda
                es_usd = 'USD' in desc.upper() or 'OPENAI' in desc.upper()
                
                # Validar que sea consumo real
                if monto > 0 and len(desc) > 2:
                    # Excluir pagos y saldos
                    if not any(palabra in desc.upper() for palabra in 
                             ['PAGO', 'TRANSFERENCIA', 'SALDO']):
                        consumo = {
                            "fecha": fecha,
                            "descripcion": desc,
                            "monto": monto,
                            "moneda": "USD" if es_usd else "ARS",
                            "banco": "MACRO"
                        }
                        consumos.append(consumo)
                
            except Exception as e:
                continue
        
        return consumos
    
    def procesar_pdf(self, pdf_path: str = None):
        """Procesa PDF de Macro Bank"""
        if not pdf_path:
            pdf_path = "resumenes/descarga.pdf"
        
        print(f"Procesando: {os.path.basename(pdf_path)}")
        
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            
            todos_los_consumos = []
            
            # Procesar primera página (donde están los consumos)
            page = pdf[0]
            pil_image = page.render(scale=3).to_pil()
            
            # Mejorar imagen
            gray = pil_image.convert('L')
            enhancer = ImageEnhance.Contrast(gray)
            contrast = enhancer.enhance(3.0)
            
            enhancer = ImageEnhance.Sharpness(contrast)
            sharp = enhancer.enhance(2.0)
            
            denoised = sharp.filter(ImageFilter.MedianFilter())
            
            # OCR
            import numpy as np
            image_array = np.array(denoised)
            
            result = self.reader.readtext(image_array, detail=0, paragraph=True)
            
            # Unir texto
            texto_completo = '\n'.join([str(line) for line in result])
            
            # Aplicar correcciones
            texto_corregido = self.corregir_texto(texto_completo)
            
            # Extraer consumos
            consumos = self.extraer_consumos(texto_corregido)
            
            if consumos:
                print(f"Encontrados {len(consumos)} consumos")
                
                # Guardar resultados
                with open("macro_consumos_extraidos.json", "w", encoding="utf-8") as f:
                    json.dump(consumos, f, indent=4, ensure_ascii=False)
                
                # Archivos separados
                ars_consumos = [c for c in consumos if c['moneda'] == 'ARS']
                usd_consumos = [c for c in consumos if c['moneda'] == 'USD']
                
                with open("macro_ars.json", "w", encoding="utf-8") as f:
                    json.dump(ars_consumos, f, indent=4, ensure_ascii=False)
                    
                with open("macro_usd.json", "w", encoding="utf-8") as f:
                    json.dump(usd_consumos, f, indent=4, ensure_ascii=False)
                
                # Mostrar resumen
                print(f"\nGuardados:")
                print(f"- macro_consumos_extraidos.json: {len(consumos)} totales")
                print(f"- macro_ars.json: {len(ars_consumos)} en pesos")
                print(f"- macro_usd.json: {len(usd_consumos)} en dólares")
                
                print(f"\nTop 10 consumos:")
                ordenados = sorted(consumos, key=lambda x: x['monto'], reverse=True)
                for i, c in enumerate(ordenados[:10], 1):
                    print(f"{i:2}. {c['fecha']} | {c['moneda']:3} {c['monto']:12,.2f} | {c['descripcion'][:50]}")
            else:
                print("No se encontraron consumos")
            
            pdf.close()
            
        except Exception as e:
            print(f"Error procesando PDF: {e}")
            return []
        
        return consumos

if __name__ == "__main__":
    # Importar PIL para ImageFilter
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        print("Instalar: pip install Pillow")
        exit(1)
    
    extractor = MacroOCR_simple()
    consumos = extractor.procesar_pdf()
    
    if consumos:
        print(f"\nEXITO: {len(consumos)} consumos extraidos correctamente")
    else:
        print("No se pudieron extraer consumos")