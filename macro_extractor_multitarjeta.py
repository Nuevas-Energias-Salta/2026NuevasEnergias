#!/usr/bin/env python3
"""
Extractor profesional para resúmenes de Banco Macro
Implementa la lógica de extracción según el prompt proporcionado
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pdfplumber
import easyocr
import numpy as np

class MacroExtractorProfesional:
    """Extractor profesional para resúmenes Banco Macro con lógica multitarjeta"""
    
    def __init__(self):
        self.reader = easyocr.Reader(['es'], gpu=False)
        
        # Mapeo de meses español -> número
        self.meses_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05',
            'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10',
            'nov': '11', 'dic': '12', 'enerc': '01', 'dicienbre': '12'
        }
        
        # Patrones de búsqueda
        self.patron_tarjeta = re.compile(r'Total\s+Cons[um]ros\s+de\s+([^\n]+?)\s+TARJET[AE]\s+(\d{4})', re.IGNORECASE)
        self.patron_consumo_simple = re.compile(r'(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+\d{2,4})?\s+(.+?)\s+(\d+[.,]\d{2})$')
        self.patron_consumo_compacto = re.compile(r'(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+\d{2,4})?\s+(\d{6})\s+(.+?)\s+(\d+[.,]\d{2})')
        self.patron_cuotas = re.compile(r'C\.(\d{2})/(\d{2})')
        self.patron_comercio = re.compile(r'(\d{6})')
        
    def extraer_texto_ocr(self, pdf_path: str) -> Optional[str]:
        """Extrae texto usando OCR optimizado para resúmenes Macro"""
        print(f"Extrayendo texto de: {pdf_path}")
        
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            
            todo_texto = []
            
            for page_num in range(len(pdf)):
                print(f"   Procesando página {page_num + 1}...")
                
                # Renderizar imagen de alta calidad
                page = pdf[page_num]
                pil_image = page.render(scale=3).to_pil()
                
                # Convertir a escala de grises para mejor OCR
                gray = pil_image.convert('L')
                
                # OCR
                image_array = np.array(gray)
                result = self.reader.readtext(image_array, detail=0, paragraph=True)
                
                # Unir texto
                texto_pagina = '\n'.join([str(line) for line in result])
                todo_texto.append(texto_pagina)
                
                # Debug: guardar texto de cada página
                with open(f"debug_pagina_{page_num+1}.txt", "w", encoding="utf-8") as f:
                    f.write(texto_pagina)
            
            pdf.close()
            
            texto_completo = '\n'.join(todo_texto)
            
            # Guardar texto completo para debug
            with open("debug_texto_completo.txt", "w", encoding="utf-8") as f:
                f.write(texto_completo)
            
            print(f"Texto extraído: {len(texto_completo)} caracteres")
            return texto_completo
            
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
    
    def identificar_tarjetas(self, texto: str) -> List[Dict]:
        """Identifica las tarjetas y sus secciones de consumos"""
        tarjetas = []
        
        # Buscar todas las líneas de "Total Consumos de"
        matches = list(self.patron_tarjeta.finditer(texto))
        
        for i, match in enumerate(matches):
            nombre = match.group(1).strip()
            numero = match.group(2).strip()
            
            # Determinar el rango de texto para esta tarjeta
            inicio = match.start()
            fin = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
            
            # Extraer sección de consumos
            seccion_consumos = texto[inicio:fin]
            
            tarjetas.append({
                'nombre': nombre,
                'numero': numero,
                'seccion': seccion_consumos,
                'inicio': inicio,
                'fin': fin
            })
            
            print(f"Tarjeta encontrada: {nombre} ****{numero}")
        
        return tarjetas
    
    def normalizar_fecha(self, dia: str, mes: str, anio_suffix: Optional[str] = None) -> str:
        """Normaliza fechas al formato DD-MM-YY"""
        dia = dia.zfill(2)
        
        mes_normalizado = self.meses_map.get(mes.lower())
        if not mes_normalizado:
            return None
        
        # Lógica de año según el prompt
        if anio_suffix:
            anio = anio_suffix[-2:]  # Tomar últimos 2 dígitos
        else:
            # Si no tiene año, asumir año actual o siguiente según lógica de negocio
            anio = '26'  # Ajustar según necesidad
        
        return f"{dia}-{mes_normalizado}-{anio}"
    
    def extraer_consumos_de_seccion(self, seccion: str, tarjeta_info: Dict) -> List[Dict]:
        """Extrae consumos de la sección de una tarjeta específica"""
        consumos = []
        lineas = seccion.split('\n')
        
        # Bandera para saber si estamos después de la línea "Total Consumos de"
        en_seccion_consumos = False
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            
            # Si encontramos la línea de totalizar, activamos la bandera
            if f"Total Consumos de {tarjeta_info['nombre']} TARJETA {tarjeta_info['numero']}" in linea:
                en_seccion_consumos = True
                continue
            
            # Si encontramos otra línea de totalizar, terminamos esta sección
            if "Total Consumos de" in linea and linea != f"Total Consumos de {tarjeta_info['nombre']} TARJETA {tarjeta_info['numero']}":
                break
            
            if not en_seccion_consumos:
                continue
            
            # Intentar extraer consumo con diferentes patrones
            consumo = self._extraer_consumo_linea(linea, tarjeta_info)
            if consumo:
                consumos.append(consumo)
        
        # También procesar bloques compactos (consumos "escondidos")
        consumos.extend(self._extraer_bloques_compactos(seccion, tarjeta_info))
        
        return consumos
    
    def _extraer_consumo_linea(self, linea: str, tarjeta_info: Dict) -> Optional[Dict]:
        """Intenta extraer un consumo de una línea individual"""
        
        # Patrón 1: Formato estándar: Fecha Mes Descripción Monto
        match1 = re.match(r'(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+\d{2,4})?\s+(.+?)\s+(\d+[.,]\d{2})$', linea)
        if match1:
            return self._construir_consumo(match1, tarjeta_info, "estandar")
        
        # Patrón 2: Formato con código de comercio: Fecha Mes Código Comercio Descripción Monto
        match2 = re.match(r'(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+\d{2,4})?\s+(\d{6})\s+(.+?)\s+(\d+[.,]\d{2})$', linea)
        if match2:
            return self._construir_consumo(match2, tarjeta_info, "con_codigo")
        
        # Patrón 3: Formato compacto (bloques densos)
        # Esto se maneja en la función separada _extraer_bloques_compactos
        
        return None
    
    def _extraer_bloques_compactos(self, seccion: str, tarjeta_info: Dict) -> List[Dict]:
        """Extrae consumos de bloques compactos/densos"""
        consumos = []
        
        # Buscar patrones compactos mencionados en el prompt
        # Ej: "TARJETA 6646 Total Consumos de MARCIA M AGUERO 439386,13 25 004977 VIUMI RENTEC 78333,33 19 Agosto C.06/06"
        
        # Patrón para encontrar secuencias de consumos compactos
        patron_compacto = re.compile(
            r'(\d{1,2})\s+([A-Za-záéíóúñ]+)(?:\s+\d{2,4})?\s+(\d{6})?\s*([^0-9]*?)\s*(\d+[.,]\d{2})(?:\s+C\.(\d{2})/(\d{2}))?'
        )
        
        matches = patron_compacto.finditer(seccion)
        
        for match in matches:
            try:
                dia = match.group(1)
                mes = match.group(2)
                codigo_comercio = match.group(3) if match.group(3) else ""
                descripcion = match.group(4).strip() if match.group(4) else ""
                monto_str = match.group(5)
                cuota_actual = match.group(6)
                cuota_total = match.group(7)
                
                # Validar y construir consumo
                if self.meses_map.get(mes.lower()) and float(monto_str.replace('.', '').replace(',', '.')) > 0:
                    
                    fecha = self.normalizar_fecha(dia, mes)
                    monto = float(monto_str.replace('.', '').replace(',', '.'))
                    
                    # Limpiar descripción
                    descripcion = descripcion.replace('*', '').strip()
                    
                    # Construir descripción completa
                    desc_completa = descripcion
                    if codigo_comercio:
                        desc_completa = f"{codigo_comercio} {descripcion}"
                    if cuota_actual and cuota_total:
                        desc_completa += f" C.{cuota_actual}/{cuota_total}"
                    
                    consumo = {
                        'fecha': fecha,
                        'descripcion': desc_completa,
                        'monto': monto,
                        'moneda': 'ARS',  # Por defecto ARS, se puede detectar USD si hay U$S
                        'tarjeta': f"{tarjeta_info['nombre']} ****{tarjeta_info['numero']}",
                        'codigo_comercio': codigo_comercio,
                        'cuotas': f"{cuota_actual}/{cuota_total}" if cuota_actual else None,
                        'tipo': 'consumo',
                        'linea_original': match.group(0),
                        'banco': 'MACRO'
                    }
                    
                    consumos.append(consumo)
                    print(f"  OK {fecha} ARS {monto:10,.2f} {desc_completa[:50]}")
                    
            except Exception as e:
                print(f"  Error procesando consumo compacto: {e}")
                continue
        
        return consumos
    
    def _construir_consumo(self, match, tarjeta_info: Dict, tipo: str) -> Dict:
        """Construye un diccionario de consumo a partir de un match"""
        
        if tipo == "estandar":
            dia = match.group(1)
            mes = match.group(2)
            descripcion = match.group(3).strip() if match.group(3) else ""
            monto_str = match.group(4)
            codigo_comercio = ""
            
        elif tipo == "con_codigo":
            dia = match.group(1)
            mes = match.group(2)
            codigo_comercio = match.group(3)
            descripcion = match.group(4).strip() if match.group(4) else ""
            monto_str = match.group(5)
        
        fecha = self.normalizar_fecha(dia, mes)
        monto = float(monto_str.replace('.', '').replace(',', '.'))
        
        # Buscar cuotas en la descripción
        cuotas_match = self.patron_cuotas.search(descripcion)
        cuotas = f"{cuotas_match.group(1)}/{cuotas_match.group(2)}" if cuotas_match else None
        
        # Limpiar descripción
        descripcion = descripcion.replace('*', '').strip()
        
        # Construir descripción completa
        desc_completa = descripcion
        if codigo_comercio:
            desc_completa = f"{codigo_comercio} {descripcion}"
        
        consumo = {
            'fecha': fecha,
            'descripcion': desc_completa,
            'monto': monto,
            'moneda': 'ARS',  # Detectar si es USD más adelante
            'tarjeta': f"{tarjeta_info['nombre']} ****{tarjeta_info['numero']}",
            'codigo_comercio': codigo_comercio,
            'cuotas': cuotas,
            'tipo': 'consumo',
            'banco': 'MACRO'
        }
        
        print(f"  OK {fecha} ARS {monto:10,.2f} {desc_completa[:50]}")
        
        return consumo
    
    def identificar_otros_cargos(self, texto: str) -> List[Dict]:
        """Identifica intereses y gastos bancarios"""
        otros_cargos = []
        
        # Patrones para otros cargos
        patrones_cargos = [
            (r'INTERESES\s+FINANCIACION', 'Intereses Financiación'),
            (r'COMIS\.\s+MANTENIMIENTO', 'Comisión Mantenimiento'),
            (r'DB\s+IVA', 'IVA Débito'),
            (r'IVA\s+DB', 'IVA Débito')
        ]
        
        for patron, descripcion in patrones_cargos:
            matches = re.finditer(fr'{patron}.*?(\d+[.,]\d{2})', texto, re.IGNORECASE)
            for match in matches:
                try:
                    monto = float(match.group(1).replace('.', '').replace(',', '.'))
                    
                    cargo = {
                        'fecha': None,  # No tienen fecha específica
                        'descripcion': descripcion,
                        'monto': monto,
                        'moneda': 'ARS',
                        'tarjeta': None,
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
        print("EXTRACTOR PROFESIONAL BANCO MACRO")
        print("=" * 60)
        
        # Paso 1: Extraer texto con OCR
        texto = self.extraer_texto_ocr(pdf_path)
        if texto is None:
            return {'error': 'No se pudo extraer texto del PDF'}
        
        # Paso 2: Identificar tarjetas
        print(f"\nIdentificando tarjetas...")
        tarjetas = self.identificar_tarjetas(texto)
        
        if not tarjetas:
            print("No se encontraron tarjetas en el resumen")
            return {'error': 'No se encontraron tarjetas'}
        
        # Paso 3: Extraer consumos por tarjeta
        todos_consumos = []
        
        for tarjeta in tarjetas:
            print(f"\nExtrayendo consumos de: {tarjeta['nombre']} ****{tarjeta['numero']}")
            consumos_tarjeta = self.extraer_consumos_de_seccion(tarjeta['seccion'], tarjeta)
            todos_consumos.extend(consumos_tarjeta)
            print(f"   OK {len(consumos_tarjeta)} consumos extraídos")
        
        # Paso 4: Identificar otros cargos
        print(f"\nIdentificando otros cargos...")
        otros_cargos = self.identificar_otros_cargos(texto)
        
        # Paso 5: Consolidar resultados
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
                    'cantidad_consumos': len(self.extraer_consumos_de_seccion(t['seccion'], t))
                }
                for t in tarjetas
            ]
        }
        
        # Guardar resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo_salida = f"macro_resumen_procesado_{timestamp}.json"
        
        with open(archivo_salida, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        
        # Mostrar resumen final
        print(f"\n" + "=" * 60)
        print(f"RESUMEN FINAL")
        print(f"=" * 60)
        print(f"Banco: MACRO")
        print(f"Fecha procesamiento: {resultado['fecha_procesamiento']}")
        print(f"Tarjetas identificadas: {resultado['tarjetas_identificadas']}")
        print(f"Total consumos: {resultado['total_consumos']}")
        print(f"Total otros cargos: {resultado['total_otros_cargos']}")
        print(f"Archivo guardado: {archivo_salida}")
        
        if todos_consumos:
            total_monto = sum(c['monto'] for c in todos_consumos)
            print(f"Total consumos ARS: {total_monto:,.2f}")
            
            print(f"\nTOP 10 CONSUMOS:")
            for i, consumo in enumerate(sorted(todos_consumos, key=lambda x: x['monto'], reverse=True)[:10], 1):
                print(f"  {i:2}. {consumo['fecha']} | ARS {consumo['monto']:12,.2f} | {consumo['descripcion'][:45]}")
        
        print("=" * 60)
        
        return resultado

def main():
    """Función principal"""
    extractor = MacroExtractorProfesional()
    
    # Ruta del PDF (ajustar según necesidad)
    pdf_path = "resumenes/descarga.pdf"
    
    # Procesar resumen
    resultado = extractor.procesar_resumen_macro(pdf_path)
    
    if 'error' in resultado:
        print(f"Error: {resultado['error']}")
    else:
        print(f"Procesamiento completado exitosamente")

if __name__ == "__main__":
    main()