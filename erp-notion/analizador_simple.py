import pdfplumber
import re
import pandas as pd
from datetime import datetime
import json

class AnalizadorFacturasSimple:
    def __init__(self):
        self.patrones_fecha = [
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
        ]
        
        self.patrones_monto = [
            r'\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'\$?\s*(\d+,\d{2})',
            r'(\d+\.\d{2})',
            r'\$(\d+(?:\.\d{3})*,\d{2})',
        ]
    
    def extraer_texto_pdf(self, ruta_pdf):
        """Extraer texto del PDF usando diferentes métodos"""
        texto_completo = ""
        
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                print(f"PDF tiene {len(pdf.pages)} páginas")
                
                for i, pagina in enumerate(pdf.pages):
                    print(f"Procesando página {i+1}...")
                    
                    # Método 1: Texto directo
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += f"\n--- PÁGINA {i+1} ---\n{texto}\n"
                        print(f"  Texto encontrado: {len(texto)} caracteres")
                        continue
                    
                    # Método 2: Extraer palabras
                    words = pagina.extract_words()
                    if words:
                        texto_palabras = " ".join([word['text'] for word in words])
                        texto_completo += f"\n--- PÁGINA {i+1} (PALABRAS) ---\n{texto_palabras}\n"
                        print(f"  Palabras encontradas: {len(words)}")
                        continue
                    
                    # Método 3: Buscar caracteres uno por uno
                    chars = pagina.chars
                    if chars:
                        texto_chars = "".join([char['text'] for char in chars])
                        texto_completo += f"\n--- PÁGINA {i+1} (CARACTERES) ---\n{texto_chars}\n"
                        print(f"  Caracteres encontrados: {len(chars)}")
                        continue
                    
                    print(f"  No se encontró texto en página {i+1}")
                    
        except Exception as e:
            print(f"Error al leer PDF: {e}")
            return None
            
        return texto_completo if texto_completo.strip() else None
    
    def parsear_linea_gasto(self, linea):
        """Parsear una línea buscando fecha, monto y concepto"""
        if len(linea.strip()) < 5:
            return None
        
        # Buscar fecha
        fecha = None
        for patron in self.patrones_fecha:
            match = re.search(patron, linea)
            if match:
                fecha = match.group(1)
                break
        
        # Buscar montos
        montos = []
        for patron in self.patrones_monto:
            matches = re.findall(patron, linea)
            for m in matches:
                # Convertir a número
                monto_str = m.replace('$', '').replace('.', '').replace(',', '.')
                try:
                    monto_num = float(monto_str)
                    if 0 < monto_num < 50000:  # Filtro de montos razonables
                        montos.append(monto_num)
                except ValueError:
                    pass
        
        if not montos:
            return None
        
        monto = montos[0]  # Tomar el primer monto válido
        
        # Extraer concepto
        concepto = linea.strip()
        
        # Remover fecha del concepto
        if fecha:
            concepto = concepto.replace(fecha, '', 1).strip()
        
        # Remover montos del concepto
        for patron in self.patrones_monto:
            matches = re.findall(patron, concepto)
            for match in matches:
                concepto = concepto.replace(match, '', 1).strip()
        
        # Limpiar concepto
        concepto = re.sub(r'\s+', ' ', concepto).strip()
        
        if len(concepto) > 3:
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
            return []
        
        print("\n" + "="*50)
        print("TEXTO EXTRAÍDO:")
        print("="*50)
        
        lineas = texto.split('\n')
        # Mostrar primeras 50 líneas para diagnóstico
        for i, linea in enumerate(lineas[:50], 1):
            print(f"{i:3d}: {repr(linea)}")
        
        print("\n" + "="*50)
        print("BUSCANDO GASTOS...")
        print("="*50)
        
        gastos = []
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if not linea:
                continue
            
            # Buscar patrones de gastos
            if (re.search(r'\d+[/.-]\d+[/.-]\d+', linea) or  # Tiene fecha
                re.search(r'\$?\d+[.,]\d{2}', linea) or     # Tiene monto
                any(palabra in linea.lower() for palabra in ['compra', 'pago', 'débito', 'consumo'])):
                
                gasto = self.parsear_linea_gasto(linea)
                if gasto:
                    gastos.append(gasto)
                    print(f"✓ Gasto #{len(gastos)}: {gasto['fecha']} - ${gasto['monto']:.2f} - {gasto['concepto']}")
        
        return gastos
    
    def guardar_resultados(self, gastos, formato='csv', archivo_salida='gastos'):
        """Guardar los gastos en el formato especificado"""
        if not gastos:
            print("No hay gastos para guardar")
            return
        
        df = pd.DataFrame(gastos)
        
        if formato.lower() == 'csv':
            df.to_csv(f'{archivo_salida}.csv', index=False, encoding='utf-8-sig')
            print(f"\n✓ Guardado en {archivo_salida}.csv")
        elif formato.lower() == 'json':
            df.to_json(f'{archivo_salida}.json', orient='records', indent=2)
            print(f"\n✓ Guardado en {archivo_salida}.json")

def main():
    analizador = AnalizadorFacturasSimple()
    ruta_pdf = r"C:\Users\Gonza\Desktop\Notion-project\resumenes\descarga.pdf"
    
    print("Analizando factura...")
    gastos = analizador.analizar_factura(ruta_pdf)
    
    if gastos:
        print(f"\nEXITO! Se encontraron {len(gastos)} gastos:")
        
        # Mostrar resumen
        print("\nRESUMEN:")
        total = sum(g['monto'] for g in gastos)
        print(f"   Total gastado: ${total:.2f}")
        print(f"   Promedio por gasto: ${total/len(gastos):.2f}")
        
        # Guardar resultados
        analizador.guardar_resultados(gastos, 'csv', 'gastos_tarjeta')
        analizador.guardar_resultados(gastos, 'json', 'gastos_tarjeta')
        
    else:
        print("\nNo se encontraron gastos.")
        print("Sugerencias:")
        print("   1. El PDF podría ser una imagen escaneada")
        print("   2. Podría necesitar ajustar los patrones de búsqueda")
        print("   3. El formato podría ser diferente al esperado")

if __name__ == "__main__":
    main()