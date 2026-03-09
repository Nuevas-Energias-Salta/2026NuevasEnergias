#!/usr/bin/env python3
"""
Interpretador de resúmenes de tarjetas de crédito con Gemini
Soporta: Banco Macro, BBVA, Galicia
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Instala google-generativeai: pip install google-generativeai")


class InterpretadorResumenes:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def detectar_banco(self, texto: str) -> str:
        """Detecta el banco basándose en el texto del resumen"""
        texto_upper = texto.upper()
        
        if "MACRO" in texto_upper or "BANCO MACRO" in texto_upper:
            return "macro"
        elif "GALICIA" in texto_upper or "BANCO GALICIA" in texto_upper:
            return "galicia"
        elif "BBVA" in texto_upper or "BANCO BBVA" in texto_upper:
            return "bbva"
        elif "SANTANDER" in texto_upper:
            return "santander"
        elif "CIUDAD" in texto_upper or "BANCO CIUDAD" in texto_upper:
            return "ciudad"
        else:
            return "desconocido"
    
    def generar_prompt_banco(self, banco: str, texto: str) -> str:
        """Genera el prompt específico para cada banco"""
        
        prompt_base = f"""Eres un experto en interpretar resúmenes de tarjetas de crédito de bancos argentinos.
Tu tarea es extraer y estructurar TODOS los movimientos del resumen de tarjeta de crédito.

BANCO: {banco.upper()}

INSTRUCCIONES:
1. Extrae TODOS los movimientos de compra, pago y cuotas
2. Para cada movimiento necesitas: fecha de operación, fecha de liquidación, descripción del comercio, monto (en pesos ARS)
3. Convierte montos en dólares a pesos usando el tipo de cambiolisted en el resumen
4. Ignora líneas de totales, subtotales y encabezados
5. Detecta si es una compra en cuotas y cuántas cuotas
6. Detecta pagos y extracciones

FORMATO DE RESPUESTA (JSON array):
[
  {{
    "fecha_operacion": "DD/MM",
    "fecha_liquidacion": "DD/MM", 
    "descripcion": "NOMBRE DEL COMERCIO O DESCRIPCION",
    "monto_ars": 12345.67,
    "monto_usd": null,
    "tipo": "compra|pago|cuota|extraccion",
    "cuotas": "1/3|2/3|3/3|null",
    "categoria": "categoria_aproximada"
  }}
]

EXTRAE TODOS LOS MOVIMIENTOS DEL SIGUIENTE TEXTO:
---
{texto[:8000]}
---

Responde SOLO con el JSON array, sin texto adicional."""

        return prompt_base
    
    def interpretar_texto(self, texto: str, banco: str = None) -> List[Dict[str, Any]]:
        """Interpreta el texto del resumen usando Gemini"""
        
        if not self.model:
            return self.interpretar_local(texto, banco)
        
        if not banco:
            banco = self.detectar_banco(texto)
        
        print(f"🏦 Banco detectado: {banco}")
        
        prompt = self.generar_prompt_banco(banco, texto)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extraer JSON de la respuesta
            response_text = response.text
            
            # Buscar JSON en la respuesta
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                movimientos = json.loads(json_match.group(0))
                return movimientos
            else:
                # Intentar parsear toda la respuesta
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return self.interpretar_local(texto, banco)
        except Exception as e:
            print(f"❌ Error con Gemini: {e}")
            return self.interpretar_local(texto, banco)
    
    def interpretar_local(self, texto: str, banco: str = None) -> List[Dict[str, Any]]:
        """Interpretación local sin Gemini (fallback)"""
        
        if not banco:
            banco = self.detectar_banco(texto)
        
        movimientos = []
        lines = texto.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Ignorar encabezados
            skip_terms = ['RESUMEN', 'PÁGINA', 'TARJETA', 'CUENTA', 'SALDO', 
                         'LÍMITE', 'PAGO', 'VENCIMIENTO', 'ESTADO', 'BANCO',
                         'IVA', 'IMPUESTO', 'TOTAL', 'SUBTOTAL', 'VISA', 
                         'MASTERCARD', 'AMEX', 'CIERRE', 'RESUMEN']
            
            if any(term in line.upper() for term in skip_terms):
                continue
            
            # Buscar monto
            amount_match = re.search(r'(\d{1,5}[.,]\d{2})', line)
            if not amount_match:
                continue
            
            # Buscar fecha
            date_match = re.search(r'(\d{1,2}[/\-]\d{1,2})', line)
            
            try:
                monto_str = amount_match.group(1).replace(',', '.')
                monto = float(monto_str)
            except:
                continue
            
            # Determinar tipo por contexto
            tipo = "compra"
            line_upper = line.upper()
            if "PAGO" in line_upper or "ABONO" in line_upper:
                tipo = "pago"
            elif "EXTRACCION" in line_upper or "RETIRO" in line_upper:
                tipo = "extraccion"
            
            # Buscar cuotas
            cuotas_match = re.search(r'(\d+)\s*/\s*(\d+)', line)
            cuotas = None
            if cuotas_match:
                cuotas = f"{cuotas_match.group(1)}/{cuotas_match.group(2)}"
            
            # Limpiar descripción
            descripcion = line
            if date_match:
                descripcion = descripcion.replace(date_match.group(0), '')
            descripcion = re.sub(r'\d{1,5}[.,]\d{2}\s*$', '', descripcion)
            descripcion = descripcion.strip()
            
            if monto > 0 and len(descripcion) > 3:
                movimiento = {
                    "fecha_operacion": date_match.group(1) if date_match else None,
                    "fecha_liquidacion": None,
                    "descripcion": descripcion[:100],
                    "monto_ars": monto,
                    "monto_usd": None,
                    "tipo": tipo,
                    "cuotas": cuotas,
                    "categoria": self.categorizar(descripcion)
                }
                movimientos.append(movimiento)
        
        return movimientos
    
    def categorizar(self, descripcion: str) -> str:
        """Categoriza un movimiento según la descripción"""
        desc_upper = descripcion.upper()
        
        categorias = {
            "supermercado": ["COTO", "CARREFOUR", "JUMBO", "DISCO", "WALMART", "CHANGOMAS", "LA ANONIMA", "VEA", "UNIMARC"],
            "restaurante": ["RESTAURANT", "BAR", "PIZZERIA", "HAMBURGUES", "MC DONALD", "BURGER", "KFC", "SUBWAY", "STARBUCKS"],
            "combustible": ["YPF", "SHELL", "AXION", "ESSO", "PETROBRAS", "NAFTA", "ESTACION"],
            "farmacia": ["FARMACIA", "FARMA", "DRUGSTORE", "BOTICA"],
            "servicios": ["EDESUR", "EDENOR", "AYSA", "TELECOM", "TELEFONO", "CELULAR", "NETFLIX", "SPOTIFY", "AMAZON"],
            "transporte": ["UBER", "CABIFY", "TAP", "AEROLINEAS", "AVIANCA", "LATAM", "ALTO", "TENE", "COLECTIVO", "SUBTE"],
            "ropa": ["ZARA", "H&M", "GAP", "ADIDAS", "NIKE", "LACOSTE", "RIPLEY", "FALABELLA", "COTO"],
            "electronica": ["FRIGORIFICO", "MUSIMUNDO", "GARBARINO", "RICH", "SAMSUNG", "APPLE", "LG"],
        }
        
        for cat, keywords in categorias.items():
            if any(kw in desc_upper for kw in keywords):
                return cat
        
        return "otros"
    
    def interpretar_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Interpreta un PDF de resumen de tarjeta"""
        
        # Extraer texto del PDF
        texto = self.extraer_texto_pdf(pdf_path)
        
        if not texto or len(texto) < 100:
            return {"error": "No se pudo extraer texto del PDF", "movimientos": []}
        
        # Detectar banco
        banco = self.detectar_banco(texto)
        
        # Interpretar movimientos
        movimientos = self.interpretar_texto(texto, banco)
        
        return {
            "banco": banco,
            "fecha_extraccion": datetime.now().isoformat(),
            "total_movimientos": len(movimientos),
            "movimientos": movimientos,
            "total_consumos": sum(m.get("monto_ars", 0) for m in movimientos if m.get("tipo") == "compra"),
            "total_pagos": sum(m.get("monto_ars", 0) for m in movimientos if m.get("tipo") == "pago")
        }
    
    def extraer_texto_pdf(self, pdf_path: str) -> str:
        """Extrae texto de un PDF usando múltiples métodos"""
        
        # Método 1: pdf2image + tesseract
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image, ImageEnhance
            
            poppler_path = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
            
            texto_completo = ""
            for image in images:
                gray = image.convert('L')
                enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
                config = '--oem 3 --psm 6 -l spa+eng'
                texto = pytesseract.image_to_string(enhanced, config=config)
                texto_completo += texto + "\n"
            
            return texto_completo
            
        except Exception as e:
            print(f"⚠️ Error con pdf2image: {e}")
        
        # Método 2: pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            texto = ""
            for page in reader.pages:
                texto += page.extract_text() + "\n"
            return texto
        except Exception as e:
            print(f"⚠️ Error con pypdf: {e}")
        
        return ""


def main():
    """Ejemplo de uso"""
    interpretador = InterpretadorResumenes()
    
    # Carpeta de resúmenes
    resumenes_dir = "resumenes"
    
    if not os.path.exists(resumenes_dir):
        print("❌ Carpeta resumenes no encontrada")
        return
    
    pdfs = [f for f in os.listdir(resumenes_dir) if f.lower().endswith('.pdf')]
    
    if not pdfs:
        print("❌ No hay PDFs en la carpeta resumenes")
        return
    
    print(f"📄 PDFs encontrados: {pdfs}")
    
    for pdf_file in pdfs:
        pdf_path = os.path.join(resumenes_dir, pdf_file)
        print(f"\n{'='*50}")
        print(f"📄 Procesando: {pdf_file}")
        print('='*50)
        
        resultado = interpretador.interpretar_pdf(pdf_path)
        
        if resultado.get("error"):
            print(f"❌ {resultado['error']}")
            continue
        
        print(f"🏦 Banco: {resultado['banco']}")
        print(f"📊 Total movimientos: {resultado['total_movimientos']}")
        print(f"💰 Consumos: ${resultado['total_consumos']:,.2f}")
        print(f"💵 Pagos: ${resultado['total_pagos']:,.2f}")
        
        # Guardar resultado
        output_file = pdf_path.replace('.pdf', '_interpretado.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guardado: {output_file}")
        
        # Mostrar primeros 5 movimientos
        print("\n📋 Primeros 5 movimientos:")
        for i, mov in enumerate(resultado['movimientos'][:5]):
            print(f"  {i+1}. {mov.get('fecha_operacion', '??/??')} | ${mov.get('monto_ars', 0):>10,.2f} | {mov.get('descripcion', '')[:40]}")


if __name__ == "__main__":
    main()
