import pdfplumber
import re
import json
import os
import sys
import io
from datetime import datetime
from typing import List, Dict, Optional
import easyocr

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class MacroBankParser:
    """Parser especializado para resúmenes de Macro Bank con OCR"""
    
    def __init__(self):
        self.reader = easyocr.Reader(['es'], gpu=False)
        print("   -> OCR EasyOCR inicializado para español")
    
    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extrae texto de PDF escaneado usando OCR"""
        print(f"   -> Extrayendo texto con OCR de: {os.path.basename(pdf_path)}")
        
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            full_text = ""
            
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                pil_image = page.render(scale=2).to_pil()
                
                # Convertir a numpy array para EasyOCR
                import numpy as np
                image_array = np.array(pil_image)
                
                # OCR
                result = self.reader.readtext(image_array, detail=0, paragraph=True)
                # Filtrar solo strings del resultado
                ocr_lines = [str(line) for line in result if line and isinstance(line, str)]
                page_text = "\n".join(ocr_lines)
                full_text += f"\n--- PÁGINA {page_num + 1} ---\n" + page_text + "\n"
                
                print(f"      -> Página {page_num + 1} procesada")
            
            pdf.close()
            return full_text
            
        except Exception as e:
            print(f"   ❌ Error en OCR: {e}")
            return ""
    
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
    
    def parse_macro_ocr(self, ocr_text: str) -> List[Dict]:
        """
        Parsea el texto OCR de Macro Bank
        Busca secciones de consumos y extrae movimientos
        """
        movements = []
        print("   -> Parseando texto OCR de Macro Bank...")
        
        # Limpiar emojis del texto OCR antes de procesar
        ocr_text = self.limpiar_emojis(ocr_text)
        
        lines = ocr_text.split('\n')
        current_titular = None
        
        # Mapeo de meses con errores comunes de OCR
        month_map = {
            'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
            'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
            'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12',
            'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05',
            'Jun': '06', 'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10',
            'Nov': '11', 'Dic': '12', 'Enerc': '01', 'Dicienbre': '12', 
            'enerc': '01', 'Enero': '01', 'Feber': '02', 'Diciembre': '12'
        }
        
        for line_num, line in enumerate(lines):
            line_clean = line.strip()
            
            # Detectar secciones de consumos por titular (corregir errores OCR)
            if any(keyword in line_clean for keyword in ["Total Consuros", "Total consumos"]):
                # Determinar titular basado en patrones detectados
                if "GABRIEL" in line_clean.upper():
                    current_titular = "GABRIEL RUIZ"
                elif "MARCIA" in line_clean.upper() or "AGUERO" in line_clean.upper():
                    current_titular = "MARCIA AGUERO"
                else:
                    current_titular = "DESCONOCIDO"
                print(f"      ✓ Sección consumos: {current_titular}")
                continue
            
            # Buscar patrones de consumos - múltiples formatos debido a errores OCR
            # Formato 1: día mes número descripción monto
            pattern1 = r'(\d{1,2})\s+([A-Za-z]+)\s+(\d+)\s+([A-Z][A-Za-z0-9\s\*\.\-]+?)\s+(\d+[.,]\d{2})$'
            
            # Formato 2: día mes descripción monto (sin número de comprobante)
            pattern2 = r'(\d{1,2})\s+([A-Za-z]+)\s+([A-Z][A-Za-z0-9\s\*\.\-]+?)\s+(\d+[.,]\d{2})$'
            
            # Formato 3: texto con USD (muy específico)
            pattern3 = r'(\d{1,2})\s+([A-Za-z]+)\s+.*?USD.*?(\d+[.,]\d{2})'
            
            for pattern in [pattern1, pattern2, pattern3]:
                match = re.search(pattern, line_clean)
                if match:
                    try:
                        groups = match.groups()
                        
                        if pattern == pattern1 and len(groups) == 5:
                            day, month, comp_num, desc, amount = groups
                        elif pattern == pattern2 and len(groups) == 4:
                            day, month, desc, amount = groups
                            comp_num = None
                        elif pattern == pattern3 and len(groups) == 3:
                            day, month, amount = groups
                            desc = "CONSUMO EN USD"
                            comp_num = None
                        else:
                            continue
                        
                        # Corregir mes con errores OCR
                        month_clean = month.strip()
                        # Corregir errores comunes
                        month_clean = month_clean.replace('Dicienbre', 'Diciembre')
                        month_clean = month_clean.replace('Enerc', 'Enero')
                        month_clean = month_clean.replace('~gosto', 'Agosto')
                        month_clean = month_clean.replace('AgOSto', 'Agosto')
                        
                        month_num = month_map.get(month_clean, '00')
                        if month_num == '00':
                            continue
                        
                        if len(day) == 1:
                            day = f'0{day}'
                        
                        # Determinar año (basado en el resumen de Ene 2026)
                        if month_num in ['12']:  # Diciembre 2025
                            year = '25'
                        else:  # Enero 2026
                            year = '26'
                        
                        fecha = f"{day}-{month_num}-{year}"
                        
                        # Convertir monto (corregir errores comunes)
                        amount_clean = amount.replace('e8', '00').replace('e6', '00')
                        amount_clean = amount_clean.replace('Z0,e8', '20,00')
                        
                        try:
                            monto = float(amount_clean.replace('.', '').replace(',', '.'))
                        except:
                            continue
                        
                        # Limpiar descripción (corregir errores OCR)
                        desc = desc.strip()
                        # Correcciones específicas
                        desc = desc.replace('HERPAGO', 'MERPAGO')
                        desc = desc.replace('MerpaGo', 'MERPAGO')
                        desc = desc.replace('MERPAGO*', 'MERPAGO*')
                        desc = desc.replace('ALMAYSRENTACA', 'ALWAYSRENTACA')
                        desc = desc.replace('ALwAYS', 'ALWAYS')
                        desc = desc.replace('alkays', 'ALWAYS')
                        desc = desc.replace('PANADERIACROCANTE', 'PANADERIA CROCANTE')
                        desc = desc.replace('JacARAKD', 'JACARANDA')
                        desc = desc.replace('SERVICAFA', 'SERVICIOS')
                        desc = desc.replace('SERVIF-', 'SERVICIOS')
                        desc = desc.replace('CoK.AR', 'COM.AR')
                        desc = desc.replace('Sanlo', 'SAN LO')
                        desc = desc.replace('Chico', 'CHICO')
                        desc = desc.replace('LactEA', 'LATAM')
                        desc = desc.replace('Faceek', 'FACEBOOK')
                        desc = desc.replace('Gridos', 'CHICO')
                        desc = desc.replace('ChaTGPT', 'CHATGPT')
                        desc = desc.replace('inismgimcusd', '')
                        
                        # Limpiar caracteres extraños
                        desc = re.sub(r'[^\w\s\*\-\.]', ' ', desc)
                        desc = re.sub(r'\s+', ' ', desc).strip()
                        
                        # Determinar moneda
                        moneda = "USD" if "USD" in line_clean.upper() else "ARS"
                        
                        # Validar que sea un consumo válido
                        if self._is_valid_consumption(desc, monto):
                            movements.append({
                                "fecha": fecha,
                                "descripcion": desc,
                                "monto": monto,
                                "moneda": moneda,
                                "banco": "MACRO",
                                "titular": current_titular,
                                "comprobante": comp_num,
                                "original": line_clean
                            })
                            print(f"      ✅ Macro: {fecha} | {moneda} {monto:,.2f} | {desc[:50]}...")
                        
                    except Exception as e:
                        print(f"      ⚠️  Error procesando línea: {line_clean} - {e}")
                        continue
        
        return movements
    
    def _is_valid_consumption(self, description: str, amount: float) -> bool:
        """Valida si es un consumo real vs pagos/saldos"""
        desc_upper = description.upper()
        
        # Excluir pagos y saldos
        payment_keywords = [
            'PAGO', 'SALDO', 'ABONO', 'CREDITO', 'DEBITO AUTOMATICO'
        ]
        
        # Excluir si parece un pago (montos negativos o muy grandes)
        if amount > 1000000:  # Más de 1 millón probablemente no es consumo normal
            return False
        
        # Si es pago/saldo, excluir
        if any(keyword in desc_upper for keyword in payment_keywords):
            return False
        
        return True

def parse_macro_with_ocr(pdf_path: str) -> List[Dict]:
    """
    Función principal para parsear PDF de Macro con OCR
    """
    print(f"\n{'='*80}")
    print(f"🏦 PROCESANDO MACRO BANK CON OCR")
    print('='*80)
    
    parser = MacroBankParser()
    
    # Extraer texto con OCR
    ocr_text = parser.extract_text_with_ocr(pdf_path)
    if not ocr_text:
        print("   ❌ No se pudo extraer texto con OCR")
        return []
    
    # Guardar texto OCR para depuración
    with open("macro_ocr_debug.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)
    print("   -> Texto OCR guardado en macro_ocr_debug.txt")
    
    # Parsear movimientos
    movements = parser.parse_macro_ocr(ocr_text)
    print(f"   -> {len(movements)} consumos extraídos de Macro Bank")
    
    return movements

# Función para integrar con el sistema principal
def parse_macro(pdf) -> List[Dict]:
    """
    Parsea resumen Macro usando OCR (compatibilidad con sistema existente)
    """
    # Como no tenemos el path directo, guardamos temporalmente y usamos OCR
    temp_path = "temp_macro.pdf"
    try:
        pdf.save(temp_path)
        movements = parse_macro_with_ocr(temp_path)
        os.remove(temp_path)
        return movements
    except Exception as e:
        print(f"   ❌ Error procesando Macro: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return []

if __name__ == "__main__":
    # Prueba directa del parser Macro
    pdf_path = "resumenes/descarga.pdf"
    if os.path.exists(pdf_path):
        movements = parse_macro_with_ocr(pdf_path)
        
        if movements:
            print(f"\n🎉 {len(movements)} CONSUMOS MACRO EXTRAÍDOS:")
            print("="*60)
            for i, m in enumerate(movements[:10], 1):  # Primeros 10
                titular_info = f" ({m['titular']})" if m.get('titular') else ""
                print(f"{i:2}. {m['fecha']} | ARS {m['monto']:10,.2f}{titular_info} | {m['descripcion'][:40]}")
            
            # Guardar resultados
            with open("macro_consumos.json", "w", encoding="utf-8") as f:
                json.dump(movements, f, indent=4, ensure_ascii=False)
            print(f"\n💾 Guardado en macro_consumos.json")
        else:
            print("❌ No se extrajeron consumos de Macro")
    else:
        print(f"❌ No se encontró: {pdf_path}")