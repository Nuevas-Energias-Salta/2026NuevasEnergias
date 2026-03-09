# -*- coding: utf-8 -*-
"""
Script para descargar automáticamente el cuadro tarifario vigente de EDESA
Usa Selenium para navegar la página y extraer datos
"""

import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuración
BASE_DIR = Path(__file__).parent
EDESA_TARIFAS_URL = "https://www.edesa.com.ar/informacion-tarifaria"  # URL principal
DOWNLOAD_DIR = BASE_DIR / "downloads_tarifas"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def configurar_driver():
    """Configura el driver de Chrome para Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Configurar carpeta de descargas
    prefs = {
        "download.default_directory": str(DOWNLOAD_DIR.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True  # Descargar PDFs en vez de abrirlos
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def esperar_descarga(carpeta, timeout=30):
    """Espera a que termine la descarga."""
    segundos = 0
    while segundos < timeout:
        time.sleep(1)
        archivos = list(Path(carpeta).glob("*"))
        # Verificar que no haya archivos .crdownload (descarga en progreso)
        if archivos and not any(f.suffix == '.crdownload' for f in archivos):
            return archivos[-1]  # Retornar último archivo descargado
        segundos += 1
    return None


def descargar_cuadro_tarifario():
    """
    Descarga el cuadro tarifario vigente desde la página de EDESA.
    Retorna: (éxito, ruta_archivo, periodo_detectado)
    """
    driver = None
    try:
        print("="*70)
        print("DESCARGADOR AUTOMÁTICO DE CUADRO TARIFARIO EDESA")
        print("="*70)
        print()
        print("🌐 Iniciando navegador...")
        
        driver = configurar_driver()
        
        # Limpiar carpeta de descargas
        for f in DOWNLOAD_DIR.glob("*"):
            f.unlink()
        
        print(f"📂 Navegando a: {EDESA_TARIFAS_URL}")
        driver.get(EDESA_TARIFAS_URL)
        time.sleep(3)
        
        # Estrategia 1: Buscar enlaces a PDFs de cuadros tarifarios
        print("🔍 Buscando cuadro tarifario vigente...")
        
        # Buscar enlaces que contengan palabras clave
        keywords = [
            "cuadro tarifario",
            "tarifas vigentes",
            "cuadro de tarifas",
            "tarifa",
            "valores vigentes"
        ]
        
        enlaces = driver.find_elements(By.TAG_NAME, "a")
        enlaces_candidatos = []
        
        for link in enlaces:
            texto = link.text.lower()
            href = link.get_attribute("href") or ""
            
            # Buscar enlaces relevantes
            if any(kw in texto for kw in keywords) or any(kw in href.lower() for kw in keywords):
                enlaces_candidatos.append({
                    'elemento': link,
                    'texto': link.text,
                    'href': href
                })
        
        print(f"   Encontrados {len(enlaces_candidatos)} enlaces candidatos")
        
        if not enlaces_candidatos:
            print("⚠️ No se encontraron enlaces directos. Intentando búsqueda en tablas...")
            
            # Estrategia 2: Buscar tablas con tarifas
            tablas = driver.find_elements(By.TAG_NAME, "table")
            if tablas:
                print(f"   Encontradas {len(tablas)} tablas en la página")
                # Aquí se podría extraer directamente de las tablas HTML
                # Por ahora, buscamos el PDF
        
        # Intentar descargar el primer enlace relevante
        archivo_descargado = None
        for candidato in enlaces_candidatos:
            href = candidato['href']
            texto = candidato['texto']
            
            print(f"📥 Intentando descargar: {texto}")
            print(f"   URL: {href}")
            
            # Si es un PDF directo
            if href.endswith('.pdf'):
                driver.get(href)
                archivo_descargado = esperar_descarga(DOWNLOAD_DIR)
                if archivo_descargado:
                    print(f"✅ Descargado: {archivo_descargado.name}")
                    break
            else:
                # Si es un enlace a página con el PDF
                try:
                    candidato['elemento'].click()
                    time.sleep(2)
                    
                    # Buscar PDF en la nueva página
                    pdfs = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
                    if pdfs:
                        pdfs[0].click()
                        archivo_descargado = esperar_descarga(DOWNLOAD_DIR)
                        if archivo_descargado:
                            print(f"✅ Descargado: {archivo_descargado.name}")
                            break
                except:
                    continue
        
        if not archivo_descargado:
            print("❌ No se pudo descargar el cuadro tarifario automáticamente")
            print("\n💡 SOLUCIÓN MANUAL:")
            print(f"   1. Ir a: {EDESA_TARIFAS_URL}")
            print(f"   2. Descargar el cuadro tarifario manualmente")
            print(f"   3. Guardarlo en: {DOWNLOAD_DIR}")
            return False, None, None
        
        # Detectar periodo del nombre del archivo
        periodo_detectado = detectar_periodo_archivo(archivo_descargado.name)
        
        print()
        print("="*70)
        print(f"✅ DESCARGA EXITOSA")
        print("="*70)
        print(f"Archivo: {archivo_descargado.name}")
        print(f"Ubicación: {archivo_descargado}")
        if periodo_detectado:
            print(f"Periodo detectado: {periodo_detectado}")
        print()
        
        return True, archivo_descargado, periodo_detectado
        
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None
    
    finally:
        if driver:
            print("🔒 Cerrando navegador...")
            driver.quit()


def detectar_periodo_archivo(nombre_archivo):
    """
    Intenta detectar el periodo del cuadro tarifario desde el nombre del archivo.
    Retorna formato: "mes YYYY"
    """
    # Patrones comunes
    # Ejemplo: "cuadro_tarifario_enero_2026.pdf"
    # Ejemplo: "tarifas_01_2026.pdf"
    
    meses_map = {
        'enero': 'ene', 'febrero': 'feb', 'marzo': 'mar', 'abril': 'abr',
        'mayo': 'may', 'junio': 'jun', 'julio': 'jul', 'agosto': 'ago',
        'septiembre': 'sep', 'octubre': 'oct', 'noviembre': 'nov', 'diciembre': 'dic',
        '01': 'ene', '02': 'feb', '03': 'mar', '04': 'abr', '05': 'may', '06': 'jun',
        '07': 'jul', '08': 'ago', '09': 'sep', '10': 'oct', '11': 'nov', '12': 'dic'
    }
    
    # Buscar patrón mes + año
    for mes_str, mes_short in meses_map.items():
        if mes_str in nombre_archivo.lower():
            # Buscar año cercano
            match = re.search(r'20\d{2}', nombre_archivo)
            if match:
                return f"{mes_short} {match.group()}"
    
    # Si no se encuentra, usar mes actual
    now = datetime.now()
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{meses[now.month - 1]} {now.year}"


def parsear_cuadro_tarifario(pdf_path):
    """
    Parsea el PDF del cuadro tarifario y extrae valores relevantes.
    Retorna diccionario con tarifas por categoría.
    
    TODO: Implementar parsing real del PDF
    Por ahora, retorna estructura vacía para completar manualmente
    """
    import pdfplumber
    
    print("📄 Parseando PDF del cuadro tarifario...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extraer texto de todas las páginas
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += page.extract_text() or ""
            
            print(f"   Extraídas {len(pdf.pages)} páginas")
            
            # Aquí iría la lógica de parsing específica
            # Por ahora, solo mostramos un resumen
            print("\n📊 Vista previa del contenido:")
            print("-" * 70)
            print(texto_completo[:500] + "...")
            print("-" * 70)
            
            print("\n⚠️ PARSING AUTOMÁTICO NO IMPLEMENTADO")
            print("   El PDF ha sido descargado correctamente.")
            print("   Debes actualizar tarifa_edesa.py manualmente por ahora.")
            
            return {}
    
    except Exception as e:
        print(f"❌ Error parseando PDF: {e}")
        return {}


def main():
    """Función principal."""
    print("\n🚀 Iniciando descarga automática de cuadro tarifario...\n")
    
    exito, archivo, periodo = descargar_cuadro_tarifario()
    
    if exito and archivo:
        print("\n📋 Próximos pasos:")
        print(f"   1. Revisar archivo descargado: {archivo}")
        print(f"   2. Actualizar tarifa_edesa.py con el periodo: {periodo}")
        print(f"   3. Actualizar valores de tarifas según el PDF")
        print(f"   4. Ejecutar: python validacion_tarifas.py")
        
        # Intentar parsear (por ahora solo muestra preview)
        if archivo.suffix == '.pdf':
            parsear_cuadro_tarifario(archivo)
    else:
        print("\n💡 Consulta GUIA_ACTUALIZACION_TARIFAS.md para proceso manual")
    
    print("\n" + "="*70)
    print("Proceso finalizado")
    print("="*70)


if __name__ == "__main__":
    main()
