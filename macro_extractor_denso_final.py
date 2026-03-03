#!/usr/bin/env python3
"""
Extractor final para resúmenes Banco Macro - Formato Denso OCR
Implementa la lógica exacta según el prompt para manejar bloques compactos
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import easyocr
import numpy as np

class MacroExtractorDenso:
    """Extractor especializado para formato denso de Banco Macro"""
    
    def __init__(self):
        self.reader = easyocr.Reader(['es'], gpu=False)
        
        # Mapeo completo de meses
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12',
            '-gosto': '08', 'agcsto': '08', 'eEnero': '01', 'eEnerc': '01'
        }
    
    def extraer_texto_ocr(self, pdf_path: str) -> Optional[str]:
        """Extrae texto usando OCR optimizado"""
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
            
            pdf.close()
            texto_completo = '\n'.join(todo_texto)
            
            print(f"Texto extraído: {len(texto_completo)} caracteres")
            return texto_completo
            
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
    
    def extraer_consumos_denso(self, texto: str) -> List[Dict]:
        """Extrae consumos de texto denso/compacto según el prompt"""
        
        # 1. Primero buscar todas las tarjetas y sus secciones
        patron_tarjeta = re.compile(
            r'TARJET[AE]R?\s+(\d{4})\s+Total\s+Consuros\s+de\s+([A-Z\s]+?)(?:\s+\d+[\d,.]*)',
            re.IGNORECASE
        )
        
        tarjetas_matches = list(patron_tarjeta.finditer(texto))
        consumos_totales = []
        
        print(f"Tarjetas detectadas: {len(tarjetas_matches)}")
        
        for i, match in enumerate(tarjetas_matches):
            # Extraer nombre y número de tarjeta
            nombre = match.group(1).strip()
            numero = match.group(2) if match.group(2) else match.group(3)
            
            print(f"\nProcesando tarjeta: {nombre} ****{numero}")
            
            # Determinar el rango de texto para esta tarjeta
            inicio_seccion = match.end()
            fin_seccion = tarjetas_matches[i + 1].start() if i + 1 < len(tarjetas_matches) else len(texto)
            
            # Extraer sección de consumos de esta tarjeta
            seccion_texto = texto[inicio_seccion:fin_seccion]
            
            # 2. Extraer consumos de esta sección
            consumos_tarjeta = self.extraer_consumos_seccion(seccion_texto, nombre, numero)
            consumos_totales.extend(consumos_tarjeta)
            
            print(f"  {len(consumos_tarjeta)} consumos encontrados")
        
        # 3. También buscar consumos antes de la primera tarjeta (consumos principales)
        if tarjetas_matches:
            seccion_principal = texto[:tarjetas_matches[0].start()]
            consumos_principales = self.extraer_consumos_seccion(seccion_principal, "TARJETA PRINCIPAL", "0000")
            consumos_totales.extend(consumos_principales)
            print(f"Consumos principales: {len(consumos_principales)}")
        
        return consumos_totales
    
    def extraer_consumos_seccion(self, texto: str, nombre_tarjeta: str, numero_tarjeta: str) -> List[Dict]:
        """Extrae consumos de una sección específica usando patrones densos"""
        
        # Patrón principal para consumos en formato denso
        # Formato: DD MES [AÑO] [CODIGO] DESCRIPCION MONTO [CUOTAS]
        patron_consumo_denso = re.compile(
            r'(\d{1,2})\s+'  # Día
            r'([A-Za-záéíóúñ-]+)'  # Mes
            r'(?:\s+(\d{2,4}))?\s*'  # Año opcional
            r'(?:'  # Inicio de opciones para código/comercio
            r'(\d{6})\s+'  # Opción 1: Código de comercio
            r'|'  # O
            r'([A-Z]+)\*'  # Opción 2: Palabra con * (ej: MERPAGO*)
            r')?\s*'  # Fin de opciones, todo opcional
            r'([^0-9]*?)\s*'  # Descripción (sin números)
            r'(\d+[.,]\d{2})'  # Monto
            r'(?:\s+C\.(\d{2})/(\d{2}))?'  # Cuotas opcionales
        )
        
        consumos = []
        matches = patron_consumo_denso.finditer(texto)
        
        for match in matches:
            try:
                dia = match.group(1)
                mes = match.group(2)
                anio = match.group(3)
                codigo_comercio = match.group(4) if match.group(4) else ""
                palabra_clave = match.group(5) if match.group(5) else ""
                descripcion = match.group(6).strip()
                monto_str = match.group(7)
                cuota_actual = match.group(8)
                cuota_total = match.group(9)
                
                # Validar mes
                mes_normalizado = self.meses_map.get(mes.lower())
                if not mes_normalizado:
                    continue
                
                # Convertir monto
                try:
                    monto = float(monto_str.replace('.', '').replace(',', '.'))
                except ValueError:
                    continue
                
                if monto <= 0:
                    continue
                
                # Formatear fecha
                dia_formateado = dia.zfill(2)
                if anio:
                    anio_formateado = anio[-2:] if len(anio) > 2 else anio
                else:
                    anio_formateado = '26'  # Año por defecto
                
                fecha = f"{dia_formateado}-{mes_normalizado}-{anio_formateado}"
                
                # Construir descripción completa
                desc_completa = descripcion
                
                # Agregar información de código/palabra clave
                if codigo_comercio:
                    desc_completa = f"{codigo_comercio} {desc_completa}"
                elif palabra_clave:
                    desc_completa = f"{palabra_clave}*{desc_completa}"
                
                # Agregar cuotas si existen
                cuotas = None
                if cuota_actual and cuota_total:
                    cuotas = f"{cuota_actual}/{cuota_total}"
                    desc_completa += f" C.{cuotas}"
                
                # Limpiar descripción
                desc_completa = re.sub(r'\s+', ' ', desc_completa).strip()
                
                # Detectar si es USD
                es_usd = ('USD' in desc_completa.upper() or 
                         'U$S' in desc_completa.upper() or 
                         'DÓLAR' in desc_completa.upper() or
                         'OPENAI' in desc_completa.upper())
                
                # Excluir líneas que no son consumos reales
                if any(palabra in desc_completa.upper() for palabra in 
                       ['SALDO', 'PAGO', 'TRANSFERENCIA', 'CUOTAS VENCER']):
                    continue
                
                consumo = {
                    'fecha': fecha,
                    'descripcion': desc_completa,
                    'monto': monto,
                    'moneda': 'USD' if es_usd else 'ARS',
                    'tarjeta': f"{nombre_tarjeta} ****{numero_tarjeta}",
                    'codigo_comercio': codigo_comercio,
                    'palabra_clave': palabra_clave,
                    'cuotas': cuotas,
                    'tipo': 'consumo',
                    'banco': 'MACRO',
                    'linea_original': match.group(0)[:100]  # Primeros 100 caracteres
                }
                
                consumos.append(consumo)
                print(f"    OK {fecha} {'USD' if es_usd else 'ARS'} {monto:10,.2f} {desc_completa[:45]}")
                
            except Exception as e:
                print(f"    Error procesando consumo: {e}")
                continue
        
        return consumos
    
    def identificar_otros_cargos(self, texto: str) -> List[Dict]:
        """Identifica intereses y gastos bancarios"""
        otros_cargos = []
        
        patrones_cargos = [
            (r'INTERESES\s+FIN[AN]CIACIO[KN].*?(\d+[.,]\d{2})', 'Intereses Financiación'),
            (r'COMIS[.\s]*MANTENIMIENTO.*?(\d+[.,]\d{2})', 'Comisión Mantenimiento'),
            (r'DB\s+IVA.*?(\d+[.,]\d{2})', 'IVA Débito'),
            (r'IVA\s+DB.*?(\d+[.,]\d{2})', 'IVA Débito'),
            (r'IIBB\s+PERCEP.*?(\d+[.,]\d{2})', 'IIBB Percepción'),
            (r'COMIS[.\s]*MANTENIMIENTO.*?\$(\d+[.,]\d{2})', 'Comisión Mantenimiento'),
            (r'IVA.*?(\d+[.,]\d{2})', 'IVA')
        ]
        
        for patron, descripcion in patrones_cargos:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                try:
                    monto_str = match.group(1)
                    monto = float(monto_str.replace('.', '').replace(',', '.'))
                    
                    if monto > 0:
                        cargo = {
                            'fecha': None,
                            'descripcion': descripcion,
                            'monto': monto,
                            'moneda': 'ARS',
                            'tipo': 'otro_cargo',
                            'banco': 'MACRO'
                        }
                        
                        otros_cargos.append(cargo)
                        print(f"    CARGO {descripcion}: ARS {monto:10,.2f}")
                        
                except Exception as e:
                    print(f"    Error procesando cargo: {e}")
        
        return otros_cargos
    
    def procesar_resumen_macro(self, pdf_path: str) -> Dict:
        """Procesamiento completo del resumen Macro"""
        print("=" * 70)
        print("EXTRACTOR BANCO MACRO - FORMATO DENSO OCR v3.0")
        print("=" * 70)
        
        # Paso 1: Extraer texto
        texto = self.extraer_texto_ocr(pdf_path)
        if texto is None:
            return {'error': 'No se pudo extraer texto del PDF'}
        
        # Guardar texto para debug
        with open("debug_texto_completo_denso.txt", "w", encoding="utf-8") as f:
            f.write(texto)
        
        # Paso 2: Extraer consumos del formato denso
        print(f"\nExtrayendo consumos del formato denso...")
        consumos = self.extraer_consumos_denso(texto)
        
        # Paso 3: Identificar otros cargos
        print(f"\nIdentificando otros cargos...")
        otros_cargos = self.identificar_otros_cargos(texto)
        
        # Paso 4: Eliminar duplicados
        consumos_unicos = []
        vistos = set()
        
        for consumo in consumos:
            clave = f"{consumo['fecha']}_{consumo['descripcion']}_{consumo['monto']}_{consumo['moneda']}"
            if clave not in vistos:
                consumos_unicos.append(consumo)
                vistos.add(clave)
        
        # Paso 5: Crear resultado
        resultado = {
            'banco': 'MACRO',
            'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_consumos': len(consumos_unicos),
            'total_otros_cargos': len(otros_cargos),
            'consumos': consumos_unicos,
            'otros_cargos': otros_cargos,
            'estadisticas': {
                'consumos_ars': len([c for c in consumos_unicos if c['moneda'] == 'ARS']),
                'consumos_usd': len([c for c in consumos_unicos if c['moneda'] == 'USD']),
                'monto_total_ars': sum(c['monto'] for c in consumos_unicos if c['moneda'] == 'ARS'),
                'monto_total_usd': sum(c['monto'] for c in consumos_unicos if c['moneda'] == 'USD')
            }
        }
        
        # Guardar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo_salida = f"macro_denso_final_{timestamp}.json"
        
        with open(archivo_salida, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        
        # Mostrar resumen completo
        self.mostrar_resumen_completo(resultado, archivo_salida)
        
        return resultado
    
    def mostrar_resumen_completo(self, resultado: Dict, archivo_salida: str):
        """Muestra un resumen detallado de los resultados"""
        print(f"\n" + "=" * 70)
        print(f"RESUMEN COMPLETO - BANCO MACRO")
        print(f"=" * 70)
        print(f"Banco: {resultado['banco']}")
        print(f"Fecha procesamiento: {resultado['fecha_procesamiento']}")
        print(f"Total consumos únicos: {resultado['total_consumos']}")
        print(f"Total otros cargos: {resultado['total_otros_cargos']}")
        print(f"Archivo guardado: {archivo_salida}")
        
        stats = resultado.get('estadisticas', {})
        print(f"\nDETALLE POR MONEDA:")
        print(f"  Consumos ARS: {stats.get('consumos_ars', 0)}")
        print(f"  Consumos USD: {stats.get('consumos_usd', 0)}")
        
        if stats.get('monto_total_ars', 0) > 0:
            print(f"  Total ARS: {stats.get('monto_total_ars', 0):,.2f}")
        if stats.get('monto_total_usd', 0) > 0:
            print(f"  Total USD: {stats.get('monto_total_usd', 0):,.2f}")
        
        if resultado['consumos']:
            print(f"\nTOP 20 CONSUMOS:")
            consumos_ordenados = sorted(resultado['consumos'], key=lambda x: x['monto'], reverse=True)
            for i, consumo in enumerate(consumos_ordenados[:20], 1):
                print(f"  {i:2}. {consumo['fecha']} | {consumo['moneda']:3} {consumo['monto']:12,.2f} | {consumo['descripcion'][:45]}")
        
        if resultado['otros_cargos']:
            print(f"\nOTROS CARGOS:")
            for i, cargo in enumerate(resultado['otros_cargos'], 1):
                print(f"  {i}. {cargo['descripcion']}: ARS {cargo['monto']:10,.2f}")
        
        print(f"\n" + "=" * 70)

def main():
    extractor = MacroExtractorDenso()
    pdf_path = "resumenes/descarga.pdf"
    
    resultado = extractor.procesar_resumen_macro(pdf_path)
    
    if 'error' in resultado:
        print(f"Error: {resultado['error']}")
    else:
        print(f"\nProcesamiento completado exitosamente")
        print(f"Consumos extraídos: {resultado['total_consumos']}")
        print(f"Otros cargos: {resultado['total_otros_cargos']}")

if __name__ == "__main__":
    main()