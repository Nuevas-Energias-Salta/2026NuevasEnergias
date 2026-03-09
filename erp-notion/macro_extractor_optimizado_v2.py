#!/usr/bin/env python3
"""
Extractor optimizado para resúmenes de Banco Macro v2.0
Implementa la lógica según el prompt con análisis línea por línea
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import easyocr
import numpy as np

class MacroExtractorOptimizado:
    """Extractor optimizado para resúmenes Banco Macro"""
    
    def __init__(self):
        self.reader = easyocr.Reader(['es'], gpu=False)
        
        # Mapeo de meses
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            '-gosto': '08', 'agcsto': '08'
        }
    
    def extraer_texto_ocr(self, pdf_path: str) -> Optional[str]:
        """Extrae texto usando OCR"""
        print(f"Extrayendo texto de: {pdf_path}")
        
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            
            todo_texto = []
            
            for page_num in range(len(pdf)):
                print(f"   Procesando página {page_num + 1}...")
                
                page = pdf[page_num]
                pil_image = page.render(scale=3).to_pil()
                gray = pil_image.convert('L')
                image_array = np.array(gray)
                
                result = self.reader.readtext(image_array, detail=0, paragraph=True)
                texto_pagina = '\n'.join([str(line) for line in result])
                todo_texto.append(texto_pagina)
                
                with open(f"debug_pagina_{page_num+1}.txt", "w", encoding="utf-8") as f:
                    f.write(texto_pagina)
            
            pdf.close()
            texto_completo = '\n'.join(todo_texto)
            
            with open("debug_texto_completo.txt", "w", encoding="utf-8") as f:
                f.write(texto_completo)
            
            print(f"Texto extraído: {len(texto_completo)} caracteres")
            return texto_completo
            
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
    
    def analizar_lineas_tarjetas(self, texto: str) -> List[Dict]:
        """Analiza el texto línea por línea para identificar tarjetas y consumos"""
        lineas = texto.split('\n')
        tarjetas = []
        tarjeta_actual = None
        
        # Patrón para detectar líneas de totalización de tarjeta
        patron_tarjeta = re.compile(r'Total\s+Cons[um]ros\s+de\s+([A-Z\s]+?)(?:\s+TARJET[AE]\s+(\d{4}))?', re.IGNORECASE)
        
        # Patrón para detectar líneas de consumos
        patron_consumo = re.compile(r'(\d{1,2})\s+([A-Za-záéíóúñ-]+)(?:\s+\d{2,4})?\s+')
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if not linea:
                continue
            
            # Buscar línea de totalización de tarjeta
            tarjeta_match = patron_tarjeta.search(linea)
            if tarjeta_match:
                # Guardar tarjeta anterior si existe
                if tarjeta_actual and tarjeta_actual['consumos']:
                    tarjetas.append(tarjeta_actual)
                
                # Extraer información de la nueva tarjeta
                nombre = tarjeta_match.group(1).strip()
                numero = tarjeta_match.group(2).strip() if tarjeta_match.group(2) else "0000"
                
                # Buscar el número de tarjeta si no está en la misma línea
                if not tarjeta_match.group(2):
                    # Buscar en la misma línea o líneas cercanas
                    patron_numero = re.search(r'TARJET[AE]\s+(\d{4})', linea.upper())
                    if patron_numero:
                        numero = patron_numero.group(1)
                    else:
                        # Buscar en líneas cercanas
                        for j in range(max(0, i-2), min(len(lineas), i+3)):
                            linea_cercana = lineas[j].upper()
                            patron_numero = re.search(r'TARJET[AE]\s+(\d{4})', linea_cercana)
                            if patron_numero:
                                numero = patron_numero.group(1)
                                break
                
                tarjeta_actual = {
                    'nombre': nombre,
                    'numero': numero,
                    'consumos': []
                }
                
                print(f"Tarjeta detectada: {nombre} ****{numero}")
                continue
            
            # Si tenemos una tarjeta activa, buscar consumos en esta línea
            if tarjeta_actual:
                consumo = self.extraer_consumo_de_linea(linea)
                if consumo:
                    consumo['tarjeta'] = f"{tarjeta_actual['nombre']} ****{tarjeta_actual['numero']}"
                    tarjeta_actual['consumos'].append(consumo)
        
        # Agregar la última tarjeta si tiene consumos
        if tarjeta_actual and tarjeta_actual['consumos']:
            tarjetas.append(tarjeta_actual)
        
        return tarjetas
    
    def extraer_consumo_de_linea(self, linea: str) -> Optional[Dict]:
        """Extrae un consumo de una línea individual"""
        
        # Patrón 1: Fecha Mes Descripción Monto
        patron1 = re.match(r'(\d{1,2})\s+([A-Za-záéíóúñ-]+)(?:\s+\d{2,4})?\s+(.+?)\s+(\d+[.,]\d{2})$', linea)
        if patron1:
            return self.construir_consumo(patron1, "simple")
        
        # Patrón 2: Fecha Mes Código Comercio Descripción Monto
        patron2 = re.match(r'(\d{1,2})\s+([A-Za-záéíóúñ-]+)(?:\s+\d{2,4})?\s+(\d{6})\s+(.+?)\s+(\d+[.,]\d{2})$', linea)
        if patron2:
            return self.construir_consumo(patron2, "con_codigo")
        
        # Patrón 3: Buscar patrones de consumo dentro de la línea (para líneas con texto mixto)
        # Buscar sub-patrones que puedan contener consumos
        patron_sub_consumo = re.finditer(r'(\d{1,2})\s+([A-Za-záéíóúñ-]+)(?:\s+\d{2,4})?\s+([^\d]*?)(\d{6})?\s*([^0-9]*?)\s*(\d+[.,]\d{2})(?:\s+C\.(\d{2})/(\d{2}))?', linea)
        
        for match in patron_sub_consumo:
            if self.meses_map.get(match.group(2).lower()):
                return self.construir_consumo(match, "subpatron")
        
        return None
    
    def construir_consumo(self, match, tipo: str) -> Dict:
        """Construye un diccionario de consumo a partir de un match"""
        
        if tipo == "simple":
            dia = match.group(1)
            mes = match.group(2)
            descripcion = match.group(3).strip()
            monto_str = match.group(4)
            codigo_comercio = ""
            
        elif tipo == "con_codigo":
            dia = match.group(1)
            mes = match.group(2)
            codigo_comercio = match.group(3)
            descripcion = match.group(4).strip()
            monto_str = match.group(5)
            
        elif tipo == "subpatron":
            dia = match.group(1)
            mes = match.group(2)
            # Ignorar grupos intermedios para subpatrones
            if len(match.groups()) >= 7:
                codigo_comercio = match.group(4) if match.group(4) else ""
                descripcion = match.group(5).strip()
                monto_str = match.group(6)
            else:
                codigo_comercio = ""
                descripcion = match.group(3).strip()
                monto_str = match.group(4)
        else:
            return None
        
        # Normalizar fecha
        mes_normalizado = self.meses_map.get(mes.lower())
        if not mes_normalizado:
            return None
        
        dia_formateado = dia.zfill(2)
        anio = '26'  # Ajustar según necesidad
        fecha = f"{dia_formateado}-{mes_normalizado}-{anio}"
        
        # Convertir monto
        try:
            monto = float(monto_str.replace('.', '').replace(',', '.'))
        except ValueError:
            return None
        
        # Buscar cuotas
        cuotas_match = re.search(r'C\.(\d{2})/(\d{2})', descripcion)
        cuotas = f"{cuotas_match.group(1)}/{cuotas_match.group(2)}" if cuotas_match else None
        
        # Limpiar descripción
        descripcion = re.sub(r'C\.\d{2}/\d{2}', '', descripcion).strip()
        descripcion = descripcion.replace('*', '').strip()
        
        # Construir descripción completa
        desc_completa = descripcion
        if codigo_comercio:
            desc_completa = f"{codigo_comercio} {descripcion}"
        if cuotas:
            desc_completa += f" C.{cuotas}"
        
        # Detectar si es USD
        es_usd = 'USD' in descripcion.upper() or 'U$S' in descripcion.upper() or 'DÓLAR' in descripcion.upper()
        
        consumo = {
            'fecha': fecha,
            'descripcion': desc_completa,
            'monto': monto,
            'moneda': 'USD' if es_usd else 'ARS',
            'codigo_comercio': codigo_comercio,
            'cuotas': cuotas,
            'tipo': 'consumo',
            'banco': 'MACRO',
            'linea_original': match.group(0) if hasattr(match, 'group') else str(match)
        }
        
        print(f"  OK {fecha} {consumo['moneda']} {monto:10,.2f} {desc_completa[:50]}")
        
        return consumo
    
    def identificar_otros_cargos(self, texto: str) -> List[Dict]:
        """Identifica intereses y gastos bancarios"""
        otros_cargos = []
        
        patrones_cargos = [
            (r'INTERESES\s+FIN[AN]CIACIO[KN]', 'Intereses Financiación'),
            (r'COMIS[.\s]*MANTENIMIENTO', 'Comisión Mantenimiento'),
            (r'DB\s+IVA', 'IVA Débito'),
            (r'IVA\s+DB', 'IVA Débito'),
            (r'IIBB\s+PERCEP', 'IIBB Percepción')
        ]
        
        for patron, descripcion in patrones_cargos:
            matches = re.finditer(fr'{patron}.*?(\d+[.,]\d{2})', texto, re.IGNORECASE)
            for match in matches:
                try:
                    monto = float(match.group(1).replace('.', '').replace(',', '.'))
                    
                    cargo = {
                        'fecha': None,
                        'descripcion': descripcion,
                        'monto': monto,
                        'moneda': 'ARS',
                        'tipo': 'otro_cargo',
                        'banco': 'MACRO'
                    }
                    
                    otros_cargos.append(cargo)
                    print(f"  CARGO {descripcion}: ARS {monto:10,.2f}")
                    
                except Exception as e:
                    print(f"  Error procesando cargo: {e}")
        
        return otros_cargos
    
    def procesar_resumen_macro(self, pdf_path: str) -> Dict:
        """Procesamiento completo del resumen Macro"""
        print("=" * 60)
        print("EXTRACTOR OPTIMIZADO BANCO MACRO v2.0")
        print("=" * 60)
        
        # Paso 1: Extraer texto
        texto = self.extraer_texto_ocr(pdf_path)
        if texto is None:
            return {'error': 'No se pudo extraer texto del PDF'}
        
        # Paso 2: Analizar líneas y extraer tarjetas/consumos
        print(f"\nAnalizando estructura del resumen...")
        tarjetas = self.analizar_lineas_tarjetas(texto)
        
        if not tarjetas:
            print("No se encontraron tarjetas con consumos")
            return {'error': 'No se encontraron consumos'}
        
        # Paso 3: Consolidar todos los consumos
        todos_consumos = []
        for tarjeta in tarjetas:
            todos_consumos.extend(tarjeta['consumos'])
            print(f"Tarjeta {tarjeta['nombre']}: {len(tarjeta['consumos'])} consumos")
        
        # Paso 4: Identificar otros cargos
        print(f"\nIdentificando otros cargos...")
        otros_cargos = self.identificar_otros_cargos(texto)
        
        # Paso 5: Crear resultado
        resultado = {
            'banco': 'MACRO',
            'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_consumos': len(todos_consumos),
            'total_otros_cargos': len(otros_cargos),
            'tarjetas_identificadas': len(tarjetas),
            'consumos': todos_consumos,
            'otros_cargos': otros_cargos,
            'resumen_tarjetas': [
                {
                    'nombre': t['nombre'],
                    'numero': t['numero'],
                    'cantidad_consumos': len(t['consumos'])
                }
                for t in tarjetas
            ]
        }
        
        # Guardar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo_salida = f"macro_optimizado_{timestamp}.json"
        
        with open(archivo_salida, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        
        # Mostrar resumen
        self.mostrar_resumen(resultado, archivo_salida)
        
        return resultado
    
    def mostrar_resumen(self, resultado: Dict, archivo_salida: str):
        """Muestra un resumen de los resultados"""
        print(f"\nRESUMEN FINAL")
        print(f"=" * 60)
        print(f"Banco: MACRO")
        print(f"Fecha procesamiento: {resultado['fecha_procesamiento']}")
        print(f"Tarjetas identificadas: {resultado['tarjetas_identificadas']}")
        print(f"Total consumos: {resultado['total_consumos']}")
        print(f"Total otros cargos: {resultado['total_otros_cargos']}")
        print(f"Archivo guardado: {archivo_salida}")
        
        if resultado['consumos']:
            total_ars = sum(c['monto'] for c in resultado['consumos'] if c['moneda'] == 'ARS')
            total_usd = sum(c['monto'] for c in resultado['consumos'] if c['moneda'] == 'USD')
            
            if total_ars > 0:
                print(f"Total consumos ARS: {total_ars:,.2f}")
            if total_usd > 0:
                print(f"Total consumos USD: {total_usd:,.2f}")
            
            print(f"\nTOP 15 CONSUMOS:")
            consumos_ordenados = sorted(resultado['consumos'], key=lambda x: x['monto'], reverse=True)
            for i, consumo in enumerate(consumos_ordenados[:15], 1):
                print(f"  {i:2}. {consumo['fecha']} | {consumo['moneda']:3} {consumo['monto']:12,.2f} | {consumo['descripcion'][:45]}")
        
        print("=" * 60)

def main():
    extractor = MacroExtractorOptimizado()
    pdf_path = "resumenes/descarga.pdf"
    
    resultado = extractor.procesar_resumen_macro(pdf_path)
    
    if 'error' in resultado:
        print(f"Error: {resultado['error']}")
    else:
        print(f"Procesamiento completado exitosamente")

if __name__ == "__main__":
    main()