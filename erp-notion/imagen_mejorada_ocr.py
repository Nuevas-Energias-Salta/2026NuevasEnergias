import sys
import os
import re
import json
from pathlib import Path

def probar_imagen_mejorada_ocr():
    """Mejorar imagen PDF antes de OCR con EasyOCR"""
    
    print("MEJORANDO IMAGEN + EASYOCR PARA MACRO")
    print("="*50)
    
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import easyocr
        import pypdfium2 as pdfium
        
        # Inicializar EasyOCR
        reader = easyocr.Reader(['es'], gpu=False)
        print("EasyOCR inicializado")
        
        # Cargar PDF
        pdf_path = "resumenes/descarga.pdf"
        pdf = pdfium.PdfDocument(pdf_path)
        
        print(f"Procesando {len(pdf)} páginas...")
        
        all_movements = []
        
        for page_num in range(len(pdf)):
            print(f"\n--- PROCESANDO PÁGINA {page_num + 1} ---")
            
            # Renderizar imagen con alta resolución
            page = pdf[page_num]
            pil_image = page.render(scale=4).to_pil()  # 4x resolucion
            
            print(f"   Imagen original: {pil_image.size}")
            
            # APLICAR MEJORAS SECUENCIALES:
            
            # 1. Convertir a escala de grises
            gray_image = pil_image.convert('L')
            print("   ✓ Convertido a escala de grises")
            
            # 2. Mejorar contraste
            enhancer = ImageEnhance.Contrast(gray_image)
            contrast_image = enhancer.enhance(2.5)  # Más contraste
            print("   ✓ Contraste mejorado")
            
            # 3. Mejorar nitidez
            enhancer = ImageEnhance.Sharpness(contrast_image)
            sharpened_image = enhancer.enhance(2.0)
            print("   ✓ Nitidez mejorada")
            
            # 4. Mejorar brillo
            enhancer = ImageEnhance.Brightness(sharpened_image)
            brightness_image = enhancer.enhance(1.1)
            print("   ✓ Brillo mejorado")
            
            # 5. Reducir ruido
            denoised_image = brightness_image.filter(ImageFilter.MedianFilter(size=1))
            print("   ✓ Ruido reducido")
            
            # 6. Binarización adaptativa (umbral)
            from PIL import ImageOps
            threshold = 200
            binary_image = denoised_image.point(lambda x: 0 if x < threshold else 255)
            print("   Binarización aplicada")
            
            # Guardar imagen mejorada para depuración
            denoised_image.save(f"pagina_{page_num + 1}_mejorada.png")
            
            # OCR con imagen mejorada
            print("   Realizando OCR con imagen mejorada...")
            result = reader.readtext(denoised_image, detail=0, paragraph=True)
            
            # Unir resultados
            ocr_text = "\n".join([str(line) for line in result])
            
            # Guardar OCR de esta página
            with open(f"pagina_{page_num + 1}_ocr_mejorado.txt", "w", encoding="utf-8") as f:
                f.write(f"--- PÁGINA {page_num + 1} OCR MEJORADO ---\n{ocr_text}\n")
            
            print(f"   OCR completado: {len(result)} líneas encontradas")
            
            # Extraer consumos del OCR mejorado
            if "SU PAGO EN PESOS" in ocr_text.upper():
                print("   Encontrado 'SU PAGO EN PESOS' - extrayendo consumos...")
                
                # Encontrar posición del pago
                pago_pos = ocr_text.upper().find("SU PAGO EN PESOS")
                texto_despues_pago = ocr_text[pago_pos + len("SU PAGO EN PESOS"):]
                
                # Extraer consumos con patrón mejorado
                patron_consumo = r'(\d{1,2})\s+([A-Za-záéíóúñ]+)\s+(\d+)\s+([A-Za-z0-9\s\*\.]+?)\s+(\d+[.,]\d{2})'
                matches = list(re.finditer(patron_consumo, texto_despues_pago))
                
                print(f"   {len(matches)} consumos potenciales encontrados")
                
                # Mapeo de meses mejorado
                month_map = {
                    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
                    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
                    'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
                    'nov': '11', 'dic': '12'
                }
                
                page_movements = []
                
                for match in matches:
                    try:
                        day = match.group(1)
                        month = match.group(2).lower()
                        num = match.group(3).strip()
                        desc = match.group(4).strip()
                        amount = match.group(5)
                        
                        # Normalizar mes
                        month_num = None
                        for mes_var, codigo in month_map.items():
                            if mes_var in month:
                                month_num = codigo
                                break
                        
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
                        
                        # Unir descripción
                        full_desc = f"{num} {desc}".strip()
                        
                        # Correcciones específicas para OCR mejorado
                        full_desc = full_desc.replace('HRTEL', 'MARTEL')
                        full_desc = full_desc.replace('HARTEL', 'MARTEL')
                        full_desc = full_desc.replace('HERPAGO', 'MERPAGO')
                        full_desc = full_desc.replace('MerpaGo', 'MERPAGO')
                        full_desc = full_desc.replace('ALMAYS', 'ALWAYS')
                        full_desc = full_desc.replace('Sanlo', 'SAN LO')
                        full_desc = full_desc.replace('Chico', 'CHICO')
                        full_desc = full_desc.replace('Faceek', 'FACEBOOK')
                        full_desc = full_desc.replace('OPENAI', 'OPENAI')
                        full_desc = full_desc.replace('LactEA', 'LATAM')
                        
                        # Limpiar
                        full_desc = re.sub(r'[^\w\s\*\-\.\/]', ' ', full_desc)
                        full_desc = re.sub(r'\s+', ' ', full_desc).strip()
                        
                        # Determinar si es USD
                        is_usd = 'USD' in full_desc.upper() or 'OPENAI' in full_desc.upper()
                        
                        if len(full_desc) > 2 and monto > 0:
                            movement = {
                                "fecha": fecha,
                                "descripcion": full_desc,
                                "monto": monto,
                                "moneda": "USD" if is_usd else "ARS",
                                "banco": "MACRO",
                                "pagina": page_num + 1,
                                "original": texto_despues_pago[match.start():match.end() + 50]
                            }
                            page_movements.append(movement)
                            print(f"      ✅ {fecha} | {'USD' if is_usd else 'ARS'} {monto:10,.2f} | {full_desc[:40]}")
                    
                    except Exception as e:
                        print(f"      ⚠️  Error procesando consumo: {e}")
                        continue
                
                print(f"   ✓ {len(page_movements)} consumos válidos extraídos de página {page_num + 1}")
                all_movements.extend(page_movements)
        
        pdf.close()
        
        # Resultado final
        print(f"\n{'='*70}")
        print(f"RESULTADO FINAL CON IMAGEN MEJORADA")
        print(f"{'='*70}")
        print(f"Total consumos extraídos: {len(all_movements)}")
        
        if all_movements:
            # Guardar resultados
            with open("macro_consumos_imagen_mejorada.json", "w", encoding="utf-8") as f:
                json.dump(all_movements, f, indent=4, ensure_ascii=False)
            
            ars_movs = [m for m in all_movements if m['moneda'] == 'ARS']
            usd_movs = [m for m in all_movements if m['moneda'] == 'USD']
            
            print(f"Archivos guardados:")
            print(f"  - macro_consumos_imagen_mejorada.json ({len(all_movements)} totales)")
            print(f"  - {len(ars_movs)} en ARS, {len(usd_movs)} en USD")
            
            print(f"\nTOP 15 CONSUMOS:")
            sorted_movs = sorted(all_movements, key=lambda x: x['monto'], reverse=True)
            for i, m in enumerate(sorted_movs[:15], 1):
                print(f"  {i:2}. {m['fecha']} | {m['moneda']:3} {m['monto']:12,.2f} | {m['descripcion'][:40]}")
        
        return all_movements
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Instalar las dependencias faltantes:")
        print("pip install pillow easyocr pypdfium2")
        return None
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        return None

if __name__ == "__main__":
    probar_imagen_mejorada_ocr()