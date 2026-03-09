import pdfplumber
import easyocr
import re
import json
import os
from datetime import datetime
from typing import List, Dict

class MacroOCRExtractor:
    """Extractor OCR profesional para resúmenes Macro Bank basado en ZZZ"""
    
    def __init__(self):
        self.reader = easyocr.Reader(['es'], gpu=False)
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
    
    def limpiar_emojis(self, texto):
        """Elimina todos los emojis para evitar errores Unicode"""
        import re
        # Patrón regex para eliminar emojis y caracteres Unicode problemáticos
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # símbolos & pictogramas
            "\U0001F680-\U0001F6FF"  # transporte y símbolos de mapas
            "\U0001F1E0-\U0001F1FF"  # banderas (iOS)
            "\U00002500-\U00002BEF"  # símbolos varios
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642" 
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+", flags=re.UNICODE
        )
        
        # Eliminar emojis y caracteres extraños
        texto_limpio = emoji_pattern.sub(r'', texto)
        
        # Eliminar caracteres de control y no imprimibles
        texto_limpio = ''.join(char for char in texto_limpio if char.isprintable() or char in ['\n', '\t'])
        
        return texto_limpio
    
    def corregir_texto_ocr(self, texto):
        """Aplica correcciones específicas de OCR basado en tu indicación"""
        # Primero limpiar emojis
        texto = self.limpiar_emojis(texto)
        
        # Corrección específica que mencionaste
        texto = texto.replace('PINTURERIAS HRTEL 49262,01', 'PINTURERIAS MARTEL 49282,01')
        
        # Otras correcciones comunes
        texto = texto.replace('HRTEL', 'MARTEL')
        texto = texto.replace('HERPAGO', 'MERPAGO')
        texto = texto.replace('MerpaGo', 'MERPAGO')
        texto = texto.replace('ALMAYS', 'ALWAYS')
        texto = texto.replace('ALMAY', 'ALWAYS')
        texto = texto.replace('ALwAYS', 'ALWAYS')
        texto = texto.replace('ALKAYS', 'ALWAYS')
        texto = texto.replace('Sanlo', 'SAN LO')
        texto = texto.replace('Chico', 'CHICO')
        texto = texto.replace('Faceek', 'FACEBOOK')
        texto = texto.replace('OPENAI', 'OPENAI')
        texto = texto.replace('ChaTGPT', 'CHATGPT')
        texto = texto.replace('LactEA', 'LATAM')
        texto = texto.replace('Gridos', 'CHICO')
        texto = texto.replace('Dicieobre', 'Octubre')
        texto = texto.replace('Diciendre', 'Diciembre')
        texto = texto.replace('~gosto', 'Agosto')
        texto = texto.replace('AgOSto', 'Agosto')
        
        return texto
    
    def extraer_consumos_despues_pago(self, texto):
        """Extrae consumos DESPUÉS de 'SU PAGO EN PESOS'"""
        # Buscar 'SU PAGO EN PESOS'
        pago_match = re.search(r'SU PAGO EN PESOS', texto.upper())
        if not pago_match:
            return []
        
        texto_despues_pago = texto[pago_match.end():]
        
        # Patrón para consumos: día mes descripción monto
        patron = r'(\d{1,2})\s+([A-Za-záéíóúñ]+)\s+([^0-9]*?)(\d+[.,]\d{2})'
        
        matches = list(re.finditer(patron, texto_despues_pago))
        consumos = []
        
        for match in matches:
            try:
                day = match.group(1).strip()
                month = match.group(2).lower().strip()
                desc_part = match.group(3).strip()
                amount = match.group(4).strip()
                
                # Normalizar mes
                month_num = self.meses_map.get(month)
                if not month_num:
                    continue
                
                # Formatear día y año
                day = f'0{day}' if len(day) == 1 else day
                year = '25' if month_num == '12' else '26'
                fecha = f"{day}-{month_num}-{year}"
                
                # Convertir monto
                monto = float(amount.replace('.', '').replace(',', '.'))
                
                # Extraer descripción limpia
                # Quitar números y montos al final
                tokens_desc = desc_part.split()
                desc_limpia = []
                
                for token in tokens_desc:
                    # Si encontramos un monto, dejamos de agregar
                    if re.match(r'^\d+$', token):
                        break
                    # Si es un monto, dejamos
                    if ',' in token and re.match(r'^\d+[.,]\d{2}$', token):
                        break
                    # Si es un número de comprobante grande
                    if re.match(r'^\d{6,}$', token):
                        continue
                    desc_limpia.append(token)
                
                desc = ' '.join(desc_limpia).strip()
                
                # Aplicar correcciones
                desc = self.corregir_texto_ocr(f"MERPAGO*{desc}")
                desc = desc.replace('MERPAGO*MERPAGO', 'MERPAGO*')
                
                # Determinar moneda
                es_usd = 'USD' in desc.upper() or 'OPENAI' in desc.upper()
                
                # Validar que sea un consumo real
                if monto > 0 and len(desc) > 2:
                    # Excluir pagos y saldos
                    if not any(palabra in desc.upper() for palabra in 
                             ['PAGO', 'TRANSFERENCIA', 'SALDO', 'INTERES', 'COMISION']):
                        
                        consumo = {
                            "fecha": fecha,
                            "descripcion": desc,
                            "monto": monto,
                            "moneda": "USD" if es_usd else "ARS",
                            "banco": "MACRO",
                            "original": texto_despues_pago[match.start():match.end() + 50]
                        }
                        consumos.append(consumo)
                        print(f"[OK] {fecha} | {'USD' if es_usd else 'ARS'} {monto:10,.2f} | {desc[:45]}")
                 
            except Exception as e:
                print(f"[!] Error procesando consumo: {e}")
                continue
        
        return consumos
    
    def procesar_pdf_macro(self, pdf_path: str = None):
        """Procesa PDF de Macro Bank con OCR"""
        if not pdf_path:
            pdf_path = "resumenes/descarga.pdf"
        
        print(f"Procesando: {os.path.basename(pdf_path)}")
        print("="*60)
        
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            
            todos_los_consumos = []
            
            for page_num in range(len(pdf)):
                print(f"\n--- Página {page_num + 1} ---")
                
                # Renderizar imagen de alta calidad
                page = pdf[page_num]
                pil_image = page.render(scale=3).to_pil()
                
                # Mejorar imagen
                gray = pil_image.convert('L')
                
                # OCR con imagen mejorada
                import numpy as np
                image_array = np.array(gray)
                
                result = self.reader.readtext(image_array, detail=0, paragraph=True)
                
                # Unir texto OCR
                texto_completo = '\n'.join([str(line) for line in result])
                
                # Aplicar correcciones
                texto_corregido = self.corregir_texto_ocr(texto_completo)
                
                # Extraer consumos
                consumos_pagina = self.extraer_consumos_despues_pago(texto_corregido)
                
                if consumos_pagina:
                    print(f"   {len(consumos_pagina)} consumos extraidos")
                    todos_los_consumos.extend(consumos_pagina)
                else:
                    print(f"   ⚠️  No se encontraron consumos")
            
            pdf.close()
            
            # Eliminar duplicados y ordenar
            consumos_unicos = []
            fechas_vistas = set()
            
            for consumo in todos_los_consumos:
                clave = f"{consumo['fecha']}_{consumo['descripcion']}_{consumo['monto']}"
                if clave not in fechas_vistas:
                    consumos_unicos.append(consumo)
                    fechas_vistas.add(clave)
            
            # Ordenar por monto (mayor a menor)
            consumos_unicos.sort(key=lambda x: x['monto'], reverse=True)
            
            print(f"\nRESULTADO FINAL")
            print(f"📊 Total consumos únicos: {len(consumos_unicos)}")
            
            if consumos_unicos:
                # Guardar resultados
                with open("macro_consumos_ocr_final.json", "w", encoding="utf-8") as f:
                    json.dump(consumos_unicos, f, indent=4, ensure_ascii=False)
                
                # Separar por moneda
                ars_consumos = [c for c in consumos_unicos if c['moneda'] == 'ARS']
                usd_consumos = [c for c in consumos_unicos if c['moneda'] == 'USD']
                
                with open("macro_ocr_ars.json", "w", encoding="utf-8") as f:
                    json.dump(ars_consumos, f, indent=4, ensure_ascii=False)
                    
                with open("macro_ocr_usd.json", "w", encoding="utf-8") as f:
                    json.dump(usd_consumos, f, indent=4, ensure_ascii=False)
                
                print(f"\n📁 Archivos guardados:")
                print(f"  📄 macro_consumos_ocr_final.json ({len(consumos_unicos)} totales)")
                print(f"  📄 macro_ocr_ars.json ({len(ars_consumos)} en pesos)")
                print(f"  📄 macro_ocr_usd.json ({len(usd_consumos)} en dólares)")
                
                # Mostrar top consumos
                print(f"\nTOP 15 CONSUMOS:")
                for i, c in enumerate(consumos_unicos[:15], 1):
                    print(f"  {i:2}. {c['fecha']} | {c['moneda']:3} {c['monto']:12,.2f} | {c['descripcion'][:45]}")
            
            return consumos_unicos
            
        except Exception as e:
            print(f"❌ Error procesando PDF: {e}")
            return []

def main():
    """Función principal del extractor Macro OCR"""
    extractor = MacroOCRExtractor()
    
    # Procesar el resumen Macro
    consumos = extractor.procesar_pdf_macro()
    
    if consumos:
        print(f"\nEXITO: {len(consumos)} consumos extraídos correctamente")
    else:
        print(f"\n❌ No se pudieron extraer consumos")

if __name__ == "__main__":
    main()