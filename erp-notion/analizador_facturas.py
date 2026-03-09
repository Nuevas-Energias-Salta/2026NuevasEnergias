import pdfplumber
import re
import pandas as pd
from datetime import datetime
import json
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class AnalizadorFacturas:
    def __init__(self):
        self.patrones_fecha = [
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{2}\d{2}\d{4})',
        ]
        
        self.patrones_monto = [
            r'\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'\$?\s*(\d+,\d{2})',
            r'(\d+\.\d{2})',
            r'(\d+,\d{2})',
        ]
    
    def extraer_texto_pdf(self, ruta_pdf):
        """Extraer texto del PDF con fallback a OCR"""
        texto_completo = ""
        
        # Intentar extracción directa primero
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += texto + "\n"
        except Exception as e:
            print(f"Error en extracción directa: {e}")
        
        # Si no hay texto y OCR está disponible, usar OCR
        if not texto_completo.strip() and OCR_AVAILABLE:
            print("Usando OCR para extraer texto...")
            try:
                imagenes = convert_from_path(ruta_pdf, dpi=300)
                for i, imagen in enumerate(imagenes):
                    texto_ocr = pytesseract.image_to_string(imagen, lang='spa')
                    texto_completo += f"\n--- PÁGINA {i+1} (OCR) ---\n{texto_ocr}\n"
            except Exception as e:
                print(f"Error en OCR: {e}")
                return None
        
        return texto_completo if texto_completo.strip() else None
    
    def parsear_linea_gasto(self, linea):
        """Parsear una línea buscando fecha, monto y concepto"""
        # Limpiar línea
        linea = ' '.join(linea.split())
        if len(linea) < 10:
            return None
        
        # Buscar fecha al inicio
        fecha = None
        resto_linea = linea
        for patron in self.patrones_fecha:
            match = re.search(patron, linea)
            if match:
                fecha = match.group(1)
                resto_linea = linea.replace(match.group(1), '', 1).strip()
                break
        
        # Buscar todos los montos en la línea
        montos_encontrados = []
        for patron in self.patrones_monto:
            matches = re.findall(patron, resto_linea)
            montos_encontrados.extend(matches)
        
        # Usar el primer monto como el gasto principal
        monto = None
        concepto = resto_linea
        
        if montos_encontrados:
            monto_str = montos_encontrados[0]
            monto_str = monto_str.replace('$', '').replace('.', '').replace(',', '.')
            try:
                monto = float(monto_str)
            except ValueError:
                pass
            
            # Remover el monto del concepto
            for patron in self.patrones_monto:
                match = re.search(patron, concepto)
                if match:
                    concepto = concepto.replace(match.group(0), '', 1).strip()
                    break
        
        # Limpiar concepto
        concepto = re.sub(r'\s+', ' ', concepto).strip()
        
        # Validar que tengamos datos útiles
        if (fecha and monto and concepto and len(concepto) > 3 and 
            monto > 0 and monto < 100000):  # Filtro de montos razonables
            return {
                'fecha': fecha,
                'monto': monto,
                'concepto': concepto
            }
        
        # Alternativa: buscar solo monto + concepto (sin fecha explícita)
        if not fecha and monto and concepto and len(concepto) > 3:
            # Intentar extraer fecha del concepto
            for patron in self.patrones_fecha:
                match = re.search(patron, concepto)
                if match:
                    fecha = match.group(1)
                    concepto = concepto.replace(match.group(1), '', 1).strip()
                    break
            
            if monto > 0 and monto < 100000:
                return {
                    'fecha': fecha or 'N/A',
                    'monto': monto,
                    'concepto': concepto
                }
        
        return None
    
    def analizar_factura(self, ruta_pdf):
        """Analizar la factura y extraer todos los gastos"""
        texto = self.extraer_texto_pdf(ruta_pdf)
        if not texto:
            print("No se pudo extraer texto del PDF")
            return []
        
        print("Texto extraído (primeras 30 líneas):")
        for i, linea in enumerate(texto.split('\n')[:30], 1):
            print(f"{i:2d}: {linea}")
        print("\n" + "="*50 + "\n")
        
        lineas = texto.split('\n')
        gastos = []
        
        # Palabras clave que indican posibles gastos
        palabras_gasto = ['compra', 'pago', 'débito', 'consumo', 'establecimiento', 'comercio']
        
        for linea in lineas:
            linea = linea.strip()
            if not linea or len(linea) < 10:
                continue
            
            # Si contiene palabras de gasto o parece una línea de gasto
            if (any(palabra in linea.lower() for palabra in palabras_gasto) or
                re.search(r'\d+[/.-]\d+[/.-]\d+', linea) or  # Tiene fecha
                re.search(r'\$?\d+[.,]\d{2}', linea)):  # Tiene monto
                
                gasto = self.parsear_linea_gasto(linea)
                if gasto:
                    gastos.append(gasto)
        
        return gastos
    
    def guardar_resultados(self, gastos, formato='csv', archivo_salida='gastos'):
        """Guardar los gastos en el formato especificado"""
        if not gastos:
            print("No hay gastos para guardar")
            return
        
        df = pd.DataFrame(gastos)
        
        if formato.lower() == 'csv':
            df.to_csv(f'{archivo_salida}.csv', index=False, encoding='utf-8-sig')
            print(f"Guardado en {archivo_salida}.csv")
        elif formato.lower() == 'json':
            df.to_json(f'{archivo_salida}.json', orient='records', indent=2, ensure_ascii=False)
            print(f"Guardado en {archivo_salida}.json")
        elif formato.lower() == 'excel':
            df.to_excel(f'{archivo_salida}.xlsx', index=False)
            print(f"Guardado en {archivo_salida}.xlsx")
        
        print(f"\nSe encontraron {len(gastos)} gastos:")
        for i, gasto in enumerate(gastos, 1):
            print(f"{i:2d}. {gasto['fecha']} - ${gasto['monto']:>8.2f} - {gasto['concepto']}")

def main():
    analizador = AnalizadorFacturas()
    
    # Analizar tu PDF
    ruta_pdf = r"C:\Users\Gonza\Desktop\Notion-project\resumenes\descarga.pdf"
    
    print("Analizando factura...")
    gastos = analizador.analizar_factura(ruta_pdf)
    
    if gastos:
        print(f"\n¡ÉXITO! Se encontraron {len(gastos)} gastos:")
        
        # Guardar en múltiples formatos
        analizador.guardar_resultados(gastos, 'csv', 'gastos_tarjeta')
        
        # Preguntar si quiere otros formatos
        print("\n¿Querés guardar en otros formatos?")
        print("1. JSON")
        print("2. Excel")
        print("3. No, solo CSV")
        
        try:
            opcion = input("Opción (1-3): ").strip()
            if opcion == '1':
                analizador.guardar_resultados(gastos, 'json', 'gastos_tarjeta')
            elif opcion == '2':
                analizador.guardar_resultados(gastos, 'excel', 'gastos_tarjeta')
        except:
            print("Guardando solo CSV...")
            
    else:
        print("No se encontraron gastos.")
        print("Podrías necesitar ajustar los patrones de búsqueda o el PDF podría tener un formato diferente.")

if __name__ == "__main__":
    main()