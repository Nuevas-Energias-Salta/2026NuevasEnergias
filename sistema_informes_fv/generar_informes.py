# -*- coding: utf-8 -*-
"""
Generador de Informes Mensuales
Crea informes HTML individuales por cada NIS con mÃ©tricas completas
"""

import os
import sys
import base64
import shutil
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Agregar path para importar mÃ³dulos del proyecto
sys.path.insert(0, str(Path(__file__).parent / "edesa_facturas" / "edesa_facturas"))

from extractor_zzz import get_sheets_service, SHEET_ID_ZZZ, SHEET_TAB_ZZZ
from nis_nombres import NIS_NOMBRES

# ================================================
# CONFIGURACIÃ“N
# ================================================

# Factores de cÃ¡lculo
FACTOR_CO2_KG_KWH = 0.45  # kg CO2 por kWh (red Argentina)
FACTOR_ARBOLES = 22  # kg CO2 que absorbe un Ã¡rbol por aÃ±o

# Rutas
BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "NE-LOGO_EES-Positivo.png"
GITHUB_REPO_DIR = BASE_DIR / "github_pages"
GITHUB_BASE_URL = os.getenv('GITHUB_PAGES_BASE', "https://administracion-ne.github.io/informes-fv/")
if not GITHUB_BASE_URL.endswith('/'): GITHUB_BASE_URL += '/'
GIT_EXE_PATH = r"C:\Program Files\Git\bin\git.exe"


# ================================================
# FUNCIONES AUXILIARES
# ================================================

def logo_to_base64():
    """Convierte el logo a base64 para embeder en HTML."""
    if not LOGO_PATH.exists():
        return None
    
    with open(LOGO_PATH, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{encoded}"


def leer_datos_sheets():
    """Lee todos los datos de la planilla ZZZ."""
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID_ZZZ,
            range=f"{SHEET_TAB_ZZZ}!A:M"  # Todas las columnas
        ).execute()
        
        values = result.get("values", [])
        if not values:
            return None
        
        # Primera fila son headers
        headers = values[0]
        data_rows = values[1:]
        
        # Convertir a lista de diccionarios
        data = []
        for row in data_rows:
            # Rellenar con vacÃ­o si faltan columnas
            row_extended = row + [""] * (len(headers) - len(row))
            data.append(dict(zip(headers, row_extended)))
        
        return data
    
    except Exception as e:
        print(f"Error leyendo datos de Sheets: {e}")
        return None


def parse_numeric(value):
    """Convierte strings con formato monetario o numÃ©rico a float."""
    if not value or value == "":
        return 0.0
    
    try:
        # Remover sÃ­mbolos de moneda, espacios, y convertir coma a punto
        cleaned = str(value).replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(cleaned)
    except:
        return 0.0


def sanitizar_url(texto):
    """Convierte un nombre a un formato amigable para URL."""
    # Validar entrada
    if not texto or str(texto).strip() == "":
        return ""  # Return empty to be caught by caller
    
    # Convertir a minÃºsculas
    texto = str(texto).lower()
    # Reemplazar acentos
    remplazos = {
        'Ã¡': 'a', 'Ã©': 'e', 'Ã­': 'i', 'Ã³': 'o', 'Ãº': 'u',
        'Ã±': 'n', 'Ã¼': 'u'
    }
    for k, v in remplazos.items():
        texto = texto.replace(k, v)
    # Remover caracteres especiales y espacios
    texto = re.sub(r'[^a-z0-9\s-]', '', texto)
    # Reemplazar espacios por guiones
    texto = re.sub(r'\s+', '-', texto).strip('-')
    
    # CRITICAL: Never return just a file extension or empty after sanitization
    if not texto or texto.startswith('.'):
        return ""
    
    return texto


def publicar_en_github(informes_generados):
    """Sube los informes generados a GitHub Pages organizados por cliente."""
    if not GITHUB_REPO_DIR.exists():
        print(f"ERROR: No se encuentra la carpeta del repositorio: {GITHUB_REPO_DIR}")
        return

    print("Subiendo informes a GitHub Pages...")
    
    # Obtener el mes actual para el histÃ³rico (formato YYYY-MM)
    fecha_hoy = datetime.now()
    mes_str = fecha_hoy.strftime("%Y-%m")

    urls_finales = []

    for info in informes_generados:
        cliente_url = sanitizar_url(info['cliente'])
        carpeta_cliente = GITHUB_REPO_DIR / cliente_url
        
        # Crear carpeta del cliente si no existe
        carpeta_cliente.mkdir(parents=True, exist_ok=True)
        
        # 1. Copiar como index.html (Ãºltimo informe)
        shutil.copy2(info['filepath'], carpeta_cliente / "index.html")
        
        # 2. Copiar como histÃ³rico (con fecha del periodo reportado)
        periodo_raw = info.get('periodo', mes_str)
        periodo_sanitizado = sanitizar_url(str(periodo_raw))
        
        # CRITICAL FIX: Ensure periodo_sanitizado is NEVER empty before using it
        if not periodo_sanitizado or periodo_sanitizado.strip() == "":
            periodo_sanitizado = f"periodo-{mes_str}"
        
        # Double-check before creating file (defense in depth)
        if periodo_sanitizado.startswith('.') or len(periodo_sanitizado) == 0:
            periodo_sanitizado = f"periodo-{mes_str}"
            
        shutil.copy2(info['filepath'], carpeta_cliente / f"{periodo_sanitizado}.html")
        
        urls_finales.append({
            'cliente': info['cliente'],
            'url': f"{GITHUB_BASE_URL}{cliente_url}/"
        })

    # Crear archivo .nojekyll (esencial para que GitHub no ignore carpetas)
    with open(GITHUB_REPO_DIR / ".nojekyll", "w") as f:
        f.write("")
    
    # Crear un index.html bÃ¡sico en la raÃ­z para que no de 404 la home
    # Agregamos timestamp para forzar a GitHub a detectar cambios
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(GITHUB_REPO_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html>\n<html lang="es">\n<head><meta charset="utf-8">')
        f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        f.write(f'<title>Portal Energetico</title></head>\n')
        f.write(f'<body><h1>Portal de Informes FV</h1><p>Ultima actualizacion: {ahora}</p>\n')
        f.write(f'<p>Navegue a /[nombre-cliente]/ para ver su informe.</p></body></html>')

    # Ejecutar comandos de Git
    try:
        # cd al repositorio
        os.chdir(GITHUB_REPO_DIR)
        
        # Git add
        subprocess.run([GIT_EXE_PATH, "add", "."], check=True, capture_output=True)
        
        # Git commit (solo si hay cambios)
        commit_msg = f"Actualizacion informes mensuales - {mes_str}"
        result = subprocess.run([GIT_EXE_PATH, "commit", "-m", commit_msg], capture_output=True)
        
        if result.returncode == 0:
            # Git push solo si hubo commit
            print("Enviando cambios a GitHub...")
            subprocess.run([GIT_EXE_PATH, "push", "origin", "main"], check=True, capture_output=True)
            print("[OK] GitHub Pages actualizado con exito!")
        elif "nothing to commit" in result.stdout.decode() or "nothing to commit" in result.stderr.decode():
            print("[INFO] No hay cambios nuevos para subir a GitHub.")
        else:
            print(f"[ERR] Error en git commit: {result.stderr.decode()}")
        print("\nLINK DE ACCESO PARA CLIENTES:")
        print("-" * 50)
        for item in urls_finales:
            print(f"{item['cliente']:<30} : {item['url']}")
        print("-" * 50)
        
    except subprocess.CalledProcessError as e:
        print(f"[ERR] Error al ejecutar comandos de Git: {e}")
        if e.stderr:
            print(f"Detalle: {e.stderr.decode()}")
    except Exception as e:
        print(f"[ERR] Error inesperado: {e}")
    finally:
        # Volver al directorio original
        os.chdir(BASE_DIR)



def calcular_metricas_nis(datos, nis):
    """
    Calcula todas las mÃ©tricas para un NIS especÃ­fico.
    Retorna dict con datos del Ãºltimo mes, acumulados histÃ³ricos, y datos para grÃ¡ficos.
    """
    # Filtrar datos de este NIS
    registros_nis = [d for d in datos if str(d.get("NIS", "")).strip() == str(nis)]
    
    if not registros_nis:
        return None
    
    # Ãšltimo registro (el mÃ¡s reciente estÃ¡ en la fila 2, primera en la lista)
    ultimo = registros_nis[0]
    
    # Extraer datos del Ãºltimo mes
    try:
        consumo_punta = parse_numeric(ultimo.get("Consumo hs punta [kWh]", 0))
        consumo_valle = parse_numeric(ultimo.get("Consumo hs valle [kWh]", 0))
        consumo_resto = parse_numeric(ultimo.get("Consumo hs resto[kWh]", 0))
        consumo_total = parse_numeric(ultimo.get("Consumo [kWh]", 0))
        generacion_fv = parse_numeric(ultimo.get("Generacion FV [kWh]", 0))
    except:
        consumo_punta = consumo_valle = consumo_resto = consumo_total = generacion_fv = 0
    
    # Calcular acumulados
    consumo_acumulado = 0
    generacion_acumulada = 0
    ahorro_acumulado = 0
    
    for reg in registros_nis:
        try:
            consumo_red = parse_numeric(reg.get("Consumo [kWh]", 0))
            gen = parse_numeric(reg.get("Generacion FV [kWh]", 0))
            
            # Consumo total = Consumo de la red + GeneraciÃ³n FV
            consumo_acumulado += consumo_red + gen
            generacion_acumulada += gen
            
            # Ahorro = GeneraciÃ³n * Tarifa Resto (aproximaciÃ³n)
            tarifa_resto = parse_numeric(reg.get("Tarifa resto", 0))
            ahorro_acumulado += gen * tarifa_resto
        except:
            pass
    
    # Impacto ambiental del Ãºltimo mes
    co2_evitado = generacion_fv * FACTOR_CO2_KG_KWH
    arboles_equivalente = co2_evitado / FACTOR_ARBOLES
    
    # FunciÃ³n para formatear fecha a nombre de mes (abreviado)
    def formatear_mes(fecha_str):
        # Abreviaturas de 3 letras
        meses_abrev = {
            "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
        }
        
        # Mapeo de abreviaturas a nÃºmeros
        mes_map = {
            'ene': '01', 'jan': '01',
            'feb': '02',
            'mar': '03',
            'abr': '04', 'apr': '04',
            'may': '05',
            'jun': '06',
            'jul': '07',
            'ago': '08', 'aug': '08',
            'sep': '09',
            'oct': '10',
            'nov': '11',
            'dic': '12', 'dec': '12'
        }
        
        try:
            fecha_lower = fecha_str.lower().strip()
            
            # Formato: "dic-2025" (mes-aÃ±o)
            if '-' in fecha_lower:
                mes_texto = fecha_lower.split('-')[0][:3]
                if mes_texto in mes_map:
                    mes_num = mes_map[mes_texto]
                    return meses_abrev.get(mes_num, fecha_str)
            
            # Formato: "Oct 2025" o "Octubre 2025"
            partes = fecha_str.split()
            if len(partes) >= 1:
                mes_texto = partes[0].lower()[:3]
                if mes_texto in mes_map:
                    mes_num = mes_map[mes_texto]
                    return meses_abrev.get(mes_num, fecha_str)
                    
        except Exception as e:
            pass
        
        return fecha_str
    
    # Datos histÃ³ricos para grÃ¡ficos TRIMESTRAL (Ãºltimos 3 meses)
    historico_labels_3m = []
    historico_consumo_3m = []
    historico_generacion_3m = []
    historico_punta_3m = []
    historico_valle_3m = []
    historico_resto_3m = []
    
    for reg in registros_nis[:3]:
        try:
            fecha = reg.get("   Fecha ", "").strip()  # 3 espacios antes, 1 despuÃ©s
            consumo = parse_numeric(reg.get("Consumo [kWh]", 0))
            gen = parse_numeric(reg.get("Generacion FV [kWh]", 0))
            punta = parse_numeric(reg.get("Consumo hs punta [kWh]", 0))
            valle = parse_numeric(reg.get("Consumo hs valle [kWh]", 0))
            resto = parse_numeric(reg.get("Consumo hs resto[kWh]", 0))
            
            historico_labels_3m.append(formatear_mes(fecha))
            historico_consumo_3m.append(consumo)
            historico_generacion_3m.append(gen)
            historico_punta_3m.append(punta)
            historico_valle_3m.append(valle)
            historico_resto_3m.append(resto)
        except:
            pass
    
    # Invertir para orden cronolÃ³gico
    historico_labels_3m.reverse()
    historico_consumo_3m.reverse()
    historico_generacion_3m.reverse()
    historico_punta_3m.reverse()
    historico_valle_3m.reverse()
    historico_resto_3m.reverse()
    
    # Datos histÃ³ricos para grÃ¡ficos ANUAL (Ãºltimos 12 meses)
    historico_labels_12m = []
    historico_consumo_12m = []
    historico_generacion_12m = []
    historico_punta_12m = []
    historico_valle_12m = []
    historico_resto_12m = []
    
    for reg in registros_nis[:12]:
        try:
            fecha = reg.get("   Fecha ", "").strip()  # 3 espacios, no 4
            consumo = parse_numeric(reg.get("Consumo [kWh]", 0))
            gen = parse_numeric(reg.get("Generacion FV [kWh]", 0))
            punta = parse_numeric(reg.get("Consumo hs punta [kWh]", 0))
            valle = parse_numeric(reg.get("Consumo hs valle [kWh]", 0))
            resto = parse_numeric(reg.get("Consumo hs resto[kWh]", 0))
            
            historico_labels_12m.append(formatear_mes(fecha))
            historico_consumo_12m.append(consumo)
            historico_generacion_12m.append(gen)
            historico_punta_12m.append(punta)
            historico_valle_12m.append(valle)
            historico_resto_12m.append(resto)
        except:
            pass
    
    # Invertir para orden cronolÃ³gico
    historico_labels_12m.reverse()
    historico_consumo_12m.reverse()
    historico_generacion_12m.reverse()
    historico_punta_12m.reverse()
    historico_valle_12m.reverse()
    historico_resto_12m.reverse()
    
    
    return {
        "cliente": ultimo.get("Cliente", "Cliente"),
        "nis": nis,
        "periodo": ultimo.get("   Fecha ", "").strip(),  # Nota: header con espacios (3 espacios)
        "categoria": ultimo.get("Catergoria", ""),  # Nota: con error de ortografÃ­a en Sheets
        
        # Datos del mes
        "consumo_punta": consumo_punta,
        "consumo_valle": consumo_valle,
        "consumo_resto": consumo_resto,
        "consumo_total": consumo_total,
        "generacion_fv": generacion_fv,
        
        # HS (pendiente: necesitamos estos datos en la planilla)
        "hs_punta": 0,
        "hs_valle": 0,
        "hs_resto": 0,
        
        # Impacto ambiental
        "co2_evitado": co2_evitado,
        "arboles": arboles_equivalente,
        
        # Ahorro del mes (aproximado)
        "ahorro_mes": generacion_fv * parse_numeric(ultimo.get("Tarifa resto", 0)),
        
        # Acumulados
        "consumo_acumulado": consumo_acumulado,
        "generacion_acumulada": generacion_acumulada,
        "ahorro_acumulado": ahorro_acumulado,
        
        # Datos para grÃ¡ficos (3 meses)
        "historico_labels_3m": historico_labels_3m,
        "historico_consumo_3m": historico_consumo_3m,
        "historico_generacion_3m": historico_generacion_3m,
        "historico_punta_3m": historico_punta_3m,
        "historico_valle_3m": historico_valle_3m,
        "historico_resto_3m": historico_resto_3m,
        
        # Datos para grÃ¡ficos (12 meses)
        "historico_labels_12m": historico_labels_12m,
        "historico_consumo_12m": historico_consumo_12m,
        "historico_generacion_12m": historico_generacion_12m,
        "historico_punta_12m": historico_punta_12m,
        "historico_valle_12m": historico_valle_12m,
        "historico_resto_12m": historico_resto_12m,
    }



# ================================================
# GENERACIÃ“N DE HTML
# ================================================

def generar_html_informe(metricas):
    """Genera el HTML del informe con grÃ¡ficos interactivos Chart.js optimizados."""
    
    logo_base64 = logo_to_base64()
    
    # Convertir imagen de Ã¡rbol a base64
    import base64
    tree_path = Path(__file__).parent / "tree_icon.png"
    tree_base64 = ""
    if tree_path.exists():
        with open(tree_path, "rb") as f:
            tree_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
    # Preparar datos para Chart.js
    import json
    
    # Datos de 3 meses
    labels_3m_json = json.dumps(metricas['historico_labels_3m'])
    resto_3m_json = json.dumps(metricas['historico_resto_3m'])
    punta_3m_json = json.dumps(metricas['historico_punta_3m'])
    valle_3m_json = json.dumps(metricas['historico_valle_3m'])
    generacion_3m_json = json.dumps(metricas['historico_generacion_3m'])
    
    # Datos de 12 meses
    labels_12m_json = json.dumps(metricas['historico_labels_12m'])
    resto_12m_json = json.dumps(metricas['historico_resto_12m'])
    punta_12m_json = json.dumps(metricas['historico_punta_12m'])
    valle_12m_json = json.dumps(metricas['historico_valle_12m'])
    generacion_12m_json = json.dumps(metricas['historico_generacion_12m'])
    
    co2_value = int(metricas['co2_evitado'])
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe FV - {metricas['cliente']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, 'Helvetica Neue', sans-serif;
            background: #C5D5CB;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: #C5D5CB;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 25px;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: bold;
            color: #000;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        
        .header .nis {{
            font-size: 13px;
            color: #555;
            font-weight: 500;
        }}
        
        .period-toggle {{
            position: absolute;
            top: 0;
            right: 0;
            display: flex;
            gap: 8px;
            background: white;
            padding: 6px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }}
        
        .period-btn {{
            padding: 8px 16px;
            border: none;
            background: transparent;
            color: #666;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        
        .period-btn.active {{
            background: #4285F4;
            color: white;
        }}
        
        .period-btn:hover:not(.active) {{
            background: #f0f0f0;
        }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 68fr 32fr;
            gap: 18px;
            margin-bottom: 18px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px 20px 30px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: relative;
            height: 450px;
        }}
        
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}
        
        .horarios-box {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-size: 11px;
            line-height: 1.8;
            color: #333;
        }}
        
        .horarios-box strong {{
            color: #000;
            font-weight: 600;
        }}
        
        .gauge-box {{
            background: white;
            padding: 25px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            position: relative;
            height: 200px;
        }}
        
        .tree-box {{
            background: white;
            padding: 22px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .tree-box img {{
            width: 100px;
            height: auto;
            margin-bottom: 12px;
            opacity: 0.9;
        }}
        
        .tree-value {{
            font-size: 36px;
            font-weight: bold;
            color: #2E7D32;
            margin-bottom: 4px;
        }}
        
        .tree-label {{
            font-size: 11px;
            color: #666;
            font-weight: 500;
        }}
        
        .factura-box {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 18px;
        }}
        
        .factura-titulo {{
            font-size: 11px;
            color: #666;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }}
        
        .factura-mes {{
            font-size: 22px;
            font-weight: bold;
            color: #000;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 18px;
        }}
        
        .metric-card-large {{
            padding: 32px 24px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            text-align: center;
            color: white;
            transition: transform 0.2s;
        }}
        
        .metric-card-large:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        .metric-card-large.consumo {{
            background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);
        }}
        
        .metric-card-large.generacion {{
            background: linear-gradient(135deg, #FFA726 0%, #F57C00 100%);
        }}
        
        .metric-card-large.ahorro {{
            background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
        }}
        
        .metric-label-large {{
            font-size: 13px;
            margin-bottom: 12px;
            opacity: 0.95;
            font-weight: 500;
            letter-spacing: 0.3px;
        }}
        
        .metric-value-large {{
            font-size: 38px;
            font-weight: bold;
            letter-spacing: -1px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .footer img {{
            max-width: 180px;
            height: auto;
            margin-bottom: 12px;
        }}
        
        .footer-text {{
            font-size: 10px;
            color: #666;
            line-height: 1.6;
        }}
        
        .data-table-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 18px;
        }}
        
        .data-table-title {{
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #333;
            text-align: center;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        
        .data-table th {{
            background: #f5f5f5;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #ddd;
        }}
        
        .data-table td {{
            padding: 8px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}
        
        .data-table tr:hover {{
            background: #f9f9f9;
        }}
        
        .data-table .month-col {{
            font-weight: 600;
            color: #333;
        }}
        
        @media (max-width: 768px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="period-toggle">
                <button class="period-btn active" onclick="switchPeriod('3m')">3 Meses</button>
                <button class="period-btn" onclick="switchPeriod('12m')">AÃ±o</button>
            </div>
            <h1 id="headerTitle">INFORME FV ÃšLTIMOS 3 MESES</h1>
            <div class="nis">NIS: {metricas['nis']} | Cliente: {metricas['cliente']} | CategorÃ­a: {metricas['categoria']}</div>
        </div>
        
        <div class="main-layout">
            <div class="chart-container">
                <canvas id="chartBarras"></canvas>
            </div>
            
            <div class="sidebar">
                <div class="horarios-box">
                    <strong>Hs Resto:</strong> 05:00 Hs - 18:00 Hs<br>
                    <strong>Hs Punta:</strong> 18:00 Hs - 23:00 Hs<br>
                    <strong>Hs Valle:</strong> 23:00 Hs - 05:00 Hs
                </div>
                
                <div class="gauge-box">
                    <canvas id="chartGauge"></canvas>
                </div>
                
                <div class="tree-box">
                    {"<img src='" + tree_base64 + "' alt='Ãrbol'>" if tree_base64 else ""}
                    <div class="tree-value">{int(metricas['arboles'])}</div>
                    <div class="tree-label">Equivalente en Ã¡rboles</div>
                </div>
            </div>
        </div>
        
        <div class="data-table-container" id="dataTableContainer">
            <div class="data-table-title">Detalle mensual</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Mes</th>
                        <th>Consumo Total (kWh)</th>
                        <th>Consumo Red (kWh)</th>
                        <th>GeneraciÃ³n FV (kWh)</th>
                        <th>% GeneraciÃ³n FV</th>
                        <th>% Consumo Red</th>
                    </tr>
                </thead>
                <tbody id="dataTableBody">
                    {''.join([f'''
                    <tr>
                        <td class="month-col">{metricas['historico_labels_3m'][i]}</td>
                        <td>{metricas['historico_consumo_3m'][i] + metricas['historico_generacion_3m'][i]:,.0f}</td>
                        <td>{metricas['historico_consumo_3m'][i]:,.0f}</td>
                        <td>{metricas['historico_generacion_3m'][i]:,.0f}</td>
                        <td>{(metricas['historico_generacion_3m'][i] / (metricas['historico_consumo_3m'][i] + metricas['historico_generacion_3m'][i]) * 100) if (metricas['historico_consumo_3m'][i] + metricas['historico_generacion_3m'][i]) > 0 else 0:.1f}%</td>
                        <td>{(metricas['historico_consumo_3m'][i] / (metricas['historico_consumo_3m'][i] + metricas['historico_generacion_3m'][i]) * 100) if (metricas['historico_consumo_3m'][i] + metricas['historico_generacion_3m'][i]) > 0 else 0:.1f}%</td>
                    </tr>''' for i in range(len(metricas['historico_labels_3m']))])}
                </tbody>
            </table>
        </div>
        
        <div class="factura-box">
            <div class="factura-titulo">Ãšltima factura considerada</div>
            <div class="factura-mes">{metricas['periodo']}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card-large consumo">
                <div class="metric-label-large">Consumo total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['consumo_acumulado']):,}</div>
            </div>
            <div class="metric-card-large generacion">
                <div class="metric-label-large">GeneraciÃ³n FV total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['generacion_acumulada']):,}</div>
            </div>
            <div class="metric-card-large ahorro">
                <div class="metric-label-large">Ahorro acumulado en $</div>
                <div class="metric-value-large">${int(metricas['ahorro_acumulado']):,}</div>
            </div>
        </div>
        
        <div class="footer">
            {"<img src='" + logo_base64 + "' alt='Nuevas EnergÃ­as'>" if logo_base64 else ""}
            <div class="footer-text">
                Fecha de la Ãºltima actualizaciÃ³n: {metricas['periodo']}<br>
                Este informe se genera automÃ¡ticamente
            </div>
        </div>
    </div>
    
    <script>
        // ConfiguraciÃ³n global de Chart.js
        Chart.defaults.font.family = 'Arial, Helvetica, sans-serif';
        Chart.defaults.color = '#333';
        
        // Datos para ambos perÃ­odos
        const data3m = {{
            labels: {labels_3m_json},
            resto: {resto_3m_json},
            punta: {punta_3m_json},
            valle: {valle_3m_json},
            generacion: {generacion_3m_json}
        }};
        
        const data12m = {{
            labels: {labels_12m_json},
            resto: {resto_12m_json},
            punta: {punta_12m_json},
            valle: {valle_12m_json},
            generacion: {generacion_12m_json}
        }};
        
        // GrÃ¡fico 1: Barras Apiladas + LÃ­nea
        const ctxBarras = document.getElementById('chartBarras').getContext('2d');
        const chartBarras = new Chart(ctxBarras, {{
            type: 'bar',
            data: {{
                labels: data3m.labels,
                datasets: [
                    {{
                        label: 'Consumo Red - hs resto',
                        data: data3m.resto,
                        backgroundColor: '#D32F2F',
                        borderWidth: 0,
                        stack: 'stack0',
                        order: 3,
                        borderRadius: {{ topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4 }}
                    }},
                    {{
                        label: 'Consumo Red - hs punta',
                        data: data3m.punta,
                        backgroundColor: '#FF9800',
                        borderWidth: 0,
                        stack: 'stack0',
                        order: 3,
                        borderRadius: 0
                    }},
                    {{
                        label: 'Consumo Red - hs valle',
                        data: data3m.valle,
                        backgroundColor: '#757575',
                        borderWidth: 0,
                        stack: 'stack0',
                        order: 3,
                        borderRadius: 0
                    }},
                    {{
                        label: 'GeneraciÃ³n FV (Autoconsumida)',
                        data: data3m.generacion,
                        backgroundColor: '#4CAF50',
                        borderWidth: 0,
                        stack: 'stack0',
                        order: 2,
                        borderRadius: {{ topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 }}
                    }},
                    {{
                        label: 'Consumo Total Real',
                        type: 'line',
                        data: data3m.labels.map((_, idx) => 
                            data3m.resto[idx] + data3m.punta[idx] + data3m.valle[idx] + data3m.generacion[idx]
                        ),
                        borderColor: '#2c3e50',
                        backgroundColor: 'rgba(0,0,0,0)',
                        borderWidth: 3,
                        borderDash: [10, 5],
                        fill: false,
                        pointRadius: 6,
                        pointBackgroundColor: '#2c3e50',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.3,
                        order: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        align: 'start',
                        labels: {{
                            font: {{ size: 11, weight: '500' }},
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 15,
                            color: '#333'
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {{ size: 13, weight: 'bold' }},
                        bodyFont: {{ size: 12 }},
                        borderColor: 'rgba(255,255,255,0.3)',
                        borderWidth: 1,
                        displayColors: true,
                        callbacks: {{
                            label: function(context) {{
                                let label = context.dataset.label || '';
                                let value = context.parsed.y;
                                
                                // Calcular total para este mes
                                let idx = context.dataIndex;
                                const currentData = context.chart.data.datasets[0].data === data3m.resto ? data3m : data12m;
                                let total = currentData.resto[idx] + currentData.punta[idx] + 
                                           currentData.valle[idx] + currentData.generacion[idx];
                                
                                // Calcular porcentaje solo para barras (no para la lÃ­nea de total)
                                if (context.dataset.type !== 'line') {{
                                    let percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': ' + value.toLocaleString('es-AR') + ' kWh (' + percentage + '%)';
                                }} else {{
                                    return label + ': ' + value.toLocaleString('es-AR') + ' kWh';
                                }}
                            }},
                            afterLabel: function(context) {{
                                // Mostrar resumen en el Ãºltimo dataset
                                if (context.datasetIndex === 4) {{
                                    let idx = context.dataIndex;
                                    const currentData = context.chart.data.datasets[0].data === data3m.resto ? data3m : data12m;
                                    let consumoRed = currentData.resto[idx] + currentData.punta[idx] + currentData.valle[idx];
                                    let genFV = currentData.generacion[idx];
                                    let total = consumoRed + genFV;
                                    let percRed = ((consumoRed / total) * 100).toFixed(1);
                                    let percFV = ((genFV / total) * 100).toFixed(1);
                                    return [
                                        '---',
                                        'Consumo Red: ' + percRed + '%',
                                        'GeneraciÃ³n FV: ' + percFV + '%'
                                    ];
                                }}
                                return '';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: true,
                        grid: {{ 
                            display: false
                        }},
                        ticks: {{
                            font: {{ size: 12, weight: '600' }},
                            color: '#000',
                            autoSkip: false,
                            maxRotation: 0,
                            minRotation: 0
                        }}
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(0,0,0,0.05)',
                            drawBorder: false
                        }},
                        ticks: {{
                            font: {{ size: 11 }},
                            color: '#555',
                            callback: function(value) {{
                                return value.toLocaleString('es-AR');
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'kWh',
                            font: {{ size: 11, weight: 'bold' }},
                            color: '#333'
                        }}
                    }}
                }}
            }}
        }});
        
        // FunciÃ³n para cambiar perÃ­odo
        function switchPeriod(period) {{
            const data = period === '3m' ? data3m : data12m;
            const title = period === '3m' ? 'INFORME FV ÃšLTIMOS 3 MESES' : 'INFORME FV ANUAL';
            
            // Actualizar tÃ­tulo
            document.getElementById('headerTitle').textContent = title;
            
            // Actualizar botones
            document.querySelectorAll('.period-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            // Actualizar datos del grÃ¡fico
            chartBarras.data.labels = data.labels;
            chartBarras.data.datasets[0].data = data.resto;
            chartBarras.data.datasets[1].data = data.punta;
            chartBarras.data.datasets[2].data = data.valle;
            chartBarras.data.datasets[3].data = data.generacion;
            // Recalcular consumo total real
            chartBarras.data.datasets[4].data = data.labels.map((_, idx) => 
                data.resto[idx] + data.punta[idx] + data.valle[idx] + data.generacion[idx]
            );
            chartBarras.update();
            
            // Actualizar tabla de datos
            const tableBody = document.getElementById('dataTableBody');
            tableBody.innerHTML = '';
            for (let i = 0; i < data.labels.length; i++) {{
                const consumoRed = data.resto[i] + data.punta[i] + data.valle[i];
                const genFV = data.generacion[i];
                const consumoTotal = consumoRed + genFV;
                const percFV = consumoTotal > 0 ? ((genFV / consumoTotal) * 100).toFixed(1) : 0;
                const percRed = consumoTotal > 0 ? ((consumoRed / consumoTotal) * 100).toFixed(1) : 0;
                const row = `
                    <tr>
                        <td class="month-col">${{data.labels[i]}}</td>
                        <td>${{Math.round(consumoTotal).toLocaleString()}}</td>
                        <td>${{Math.round(consumoRed).toLocaleString()}}</td>
                        <td>${{Math.round(genFV).toLocaleString()}}</td>
                        <td>${{percFV}}%</td>
                        <td>${{percRed}}%</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            }}
        }}
        
        // GrÃ¡fico 2: Gauge COâ‚‚
        const ctxGauge = document.getElementById('chartGauge').getContext('2d');
        const gaugeData = {{
            datasets: [{{
                data: [60, 40],
                backgroundColor: ['#4285F4', '#E8E8E8'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }}]
        }};
        
        new Chart(ctxGauge, {{
            type: 'doughnut',
            data: gaugeData,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ enabled: false }}
                }}
            }},
            plugins: [{{
                afterDraw: function(chart) {{
                    const ctx = chart.ctx;
                    const width = chart.width;
                    const height = chart.height;
                    
                    ctx.restore();
                    ctx.font = 'bold 32px Arial';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#000';
                    ctx.textAlign = 'center';
                    
                    const text = '{co2_value:,}'.replace(/,/g, '.');
                    ctx.fillText(text, width / 2, height / 2 - 5);
                    
                    ctx.font = '11px Arial';
                    ctx.fillStyle = '#666';
                    ctx.fillText('kg CO2e evitados', width / 2, height / 2 + 25);
                    
                    ctx.save();
                }}
            }}]
        }});
    </script>
</body>
</html>
"""
    
    return html
    """Genera el HTML del informe con grÃ¡ficos matplotlib."""
    
    import matplotlib
    matplotlib.use('Agg')  # Backend sin interfaz grÃ¡fica
    import matplotlib.pyplot as plt
    import io
    import base64
    
    logo_base64 = logo_to_base64()
    
    # Convertir imagen de Ã¡rbol a base64
    tree_path = Path(__file__).parent / "tree_icon.png"
    tree_base64 = ""
    if tree_path.exists():
        with open(tree_path, "rb") as f:
            tree_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
    # ============================================
    # GRÃFICO 1: Barras Apiladas + LÃ­nea
    # ============================================
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    
    labels = metricas['historico_labels']
    x = range(len(labels))
    
    # Datos
    resto = metricas['historico_resto']
    punta = metricas['historico_punta']
    valle = metricas['historico_valle']
    generacion = metricas['historico_generacion']
    
    # Barras apiladas
    ax1.bar(x, resto, label='Consumo hs resto [kWh]', color='#D32F2F', width=0.6)
    ax1.bar(x, punta, bottom=resto, label='Consumo hs punta [kWh]', color='#FF9800', width=0.6)
    
    # Calcular bottom para valle (resto + punta)
    bottom_valle = [r + p for r, p in zip(resto, punta)]
    ax1.bar(x, valle, bottom=bottom_valle, label='Consumo hs valle [kWh]', color='#757575', width=0.6)
    
    # LÃ­nea de generaciÃ³n
    ax1.plot(x, generacion, label='GeneraciÃ³n FV [kWh]', color='#000000', 
             linewidth=2, marker='o', markersize=6, zorder=10)
    
    # ConfiguraciÃ³n
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10)
    ax1.set_ylabel('GeneraciÃ³n y Consumo en kWh', fontsize=10)
    ax1.set_title('', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # Formato de miles en el eje Y
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', '.')))
    
    plt.tight_layout()
    
    # Convertir a base64
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf1.seek(0)
    chart1_base64 = "data:image/png;base64," + base64.b64encode(buf1.read()).decode()
    plt.close(fig1)
    
    # ============================================
    # GRÃFICO 2: Gauge COâ‚‚ (SemicÃ­rculo)
    # ============================================
    fig2, ax2 = plt.subplots(figsize=(4, 3), subplot_kw={'projection': 'polar'})
    
    co2_value = int(metricas['co2_evitado'])
    co2_max = max(5000, co2_value * 1.2)
    co2_percent = (co2_value / co2_max) * 100
    
    # Crear gauge semicircular
    theta = [0, (co2_percent / 100) * 180, 180]  # 0 a 180 grados (semicÃ­rculo)
    radii = [1, 1, 1]
    width = [0.4, 0.4, 0.4]
    colors = ['#E0E0E0', '#4285F4', '#E0E0E0']
    
    # Dibujar arcos
    theta_filled = (co2_percent / 100) * 3.14159  # radianes
    theta_empty = 3.14159 - theta_filled
    
    ax2.barh(0, theta_filled, left=0, height=0.3, color='#4285F4')
    ax2.barh(0, theta_empty, left=theta_filled, height=0.3, color='#E0E0E0')
    
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_theta_direction(-1)
    ax2.set_theta_zero_location('W')
    ax2.set_thetamin(0)
    ax2.set_thetamax(180)
    ax2.axis('off')
    
    # AÃ±adir texto en el centro
    ax2.text(0, -0.2, f'{co2_value:,}'.replace(',', '.'), 
             ha='center', va='center', fontsize=24, fontweight='bold',
             transform=ax2.transAxes)
    ax2.text(0, -0.35, 'kg CO2e evitados', 
             ha='center', va='center', fontsize=9, color='#666',
             transform=ax2.transAxes)
    
    plt.tight_layout()
    
    # Convertir a base64
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png', dpi=120, bbox_inches='tight', facecolor='white')
    buf2.seek(0)
    chart2_base64 = "data:image/png;base64," + base64.b64encode(buf2.read()).decode()
    plt.close(fig2)
    
    # ============================================
    # HTML
    # ============================================
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe FV - {metricas['cliente']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, 'Helvetica Neue', sans-serif;
            background: #C5D5CB;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #C5D5CB;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin-bottom: 10px;
        }}
        
        .header .nis {{
            font-size: 14px;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 7fr 3fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-container {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
        
        .chart-container img {{
            width: 100%;
            height: auto;
        }}
        
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .horarios-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
        }}
        
        .gauge-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .gauge-box img {{
            width: 100%;
            max-width: 250px;
            height: auto;
            margin: 0 auto;
        }}
        
        .tree-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .tree-box img {{
            width: 120px;
            height: auto;
            margin-bottom: 10px;
        }}
        
        .tree-value {{
            font-size: 32px;
            font-weight: bold;
            color: #000;
        }}
        
        .tree-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .factura-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .factura-titulo {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .factura-mes {{
            font-size: 24px;
            font-weight: bold;
            color: #000;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric-card-large {{
            padding: 30px 20px;
            border-radius: 4px;
            text-align: center;
            color: white;
        }}
        
        .metric-card-large.consumo {{
            background: #D32F2F;
        }}
        
        .metric-card-large.generacion {{
            background: #FFA726;
        }}
        
        .metric-card-large.ahorro {{
            background: #66BB6A;
        }}
        
        .metric-label-large {{
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.95;
        }}
        
        .metric-value-large {{
            font-size: 36px;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 4px;
        }}
        
        .footer img {{
            max-width: 200px;
            height: auto;
        }}
        
        .footer-text {{
            font-size: 11px;
            color: #666;
            margin-top: 10px;
        }}
        
        @media (max-width: 768px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>INFORME FV ÃšLTIMOS 3 MESES</h1>
            <div class="nis">NIS: {metricas['nis']} | Cliente: {metricas['cliente']} | CategorÃ­a: {metricas['categoria']}</div>
        </div>
        
        <div class="main-layout">
            <div class="chart-container">
                <img src="{chart1_base64}" alt="GrÃ¡fico de Consumo y GeneraciÃ³n">
            </div>
            
            <div class="sidebar">
                <div class="horarios-box">
                    <strong>Hs Resto:</strong> 05:00 Hs - 18:00 Hs<br>
                    <strong>Hs Punta:</strong> 18:00 Hs - 23:00 Hs<br>
                    <strong>Hs Valle:</strong> 23:00 Hs - 05:00 Hs
                </div>
                
                <div class="gauge-box">
                    <img src="{chart2_base64}" alt="COâ‚‚ Evitado">
                </div>
                
                <div class="tree-box">
                    {"<img src='" + tree_base64 + "' alt='Ãrbol'>" if tree_base64 else ""}
                    <div class="tree-value">{int(metricas['arboles'])}</div>
                    <div class="tree-label">Equivalente en Ã¡rboles</div>
                </div>
            </div>
        </div>
        
        <div class="factura-box">
            <div class="factura-titulo">Ãšltima factura considerada</div>
            <div class="factura-mes">{metricas['periodo']}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card-large consumo">
                <div class="metric-label-large">Consumo total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['consumo_acumulado']):,}</div>
            </div>
            <div class="metric-card-large generacion">
                <div class="metric-label-large">GeneraciÃ³n FV total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['generacion_acumulada']):,}</div>
            </div>
            <div class="metric-card-large ahorro">
                <div class="metric-label-large">Ahorro acumulado en $</div>
                <div class="metric-value-large">${int(metricas['ahorro_acumulado']):,}</div>
            </div>
        </div>
        
        <div class="footer">
            {"<img src='" + logo_base64 + "' alt='Nuevas EnergÃ­as'>" if logo_base64 else ""}
            <div class="footer-text">
                Fecha de la Ãºltima actualizaciÃ³n: {metricas['periodo']}<br>
                Este informe se genera automÃ¡ticamente
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html
    """Genera el HTML del informe con grÃ¡ficos interactivos Chart.js."""
    
    logo_base64 = logo_to_base64()
    
    # Convertir imagen de Ã¡rbol a base64
    import base64
    tree_path = Path(__file__).parent / "tree_icon.png"
    tree_base64 = ""
    if tree_path.exists():
        with open(tree_path, "rb") as f:
            tree_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
    # Preparar datos para Chart.js
    import json
    
    # JSON para los datasets
    labels_json = json.dumps(metricas['historico_labels'])
    resto_json = json.dumps(metricas['historico_resto'])
    punta_json = json.dumps(metricas['historico_punta'])
    valle_json = json.dumps(metricas['historico_valle'])
    generacion_json = json.dumps(metricas['historico_generacion'])
    
    # Valor CO2 para el gauge
    co2_value = int(metricas['co2_evitado'])
    co2_max = max(5000, co2_value * 1.2)  # Escala dinÃ¡mica
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe FV - {metricas['cliente']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, 'Helvetica Neue', sans-serif;
            background: #C5D5CB;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #C5D5CB;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin-bottom: 10px;
        }}
        
        .header .nis {{
            font-size: 14px;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .main-layout {{
            display: grid;
            grid-template-columns: 7fr 3fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-container {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            position: relative;
            height: 400px;
        }}
        
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .horarios-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
        }}
        
        .gauge-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
            position: relative;
            height: 200px;
        }}
        
        .tree-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}
        
        .tree-content {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .tree-box img {{
            width: 80px;
            height: auto;
        }}
        
        .tree-value {{
            font-size: 42px;
            font-weight: bold;
            color: #2E7D32;
        }}
        
        .tree-label {{
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        
        .factura-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .factura-titulo {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .factura-mes {{
            font-size: 24px;
            font-weight: bold;
            color: #000;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric-card-large {{
            padding: 30px 20px;
            border-radius: 4px;
            text-align: center;
            color: white;
        }}
        
        .metric-card-large.consumo {{
            background: #D32F2F;
        }}
        
        .metric-card-large.generacion {{
            background: #FFA726;
        }}
        
        .metric-card-large.ahorro {{
            background: #66BB6A;
        }}
        
        .metric-label-large {{
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.95;
        }}
        
        .metric-value-large {{
            font-size: 36px;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 4px;
        }}
        
        .footer img {{
            max-width: 200px;
            height: auto;
        }}
        
        .footer-text {{
            font-size: 11px;
            color: #666;
            margin-top: 10px;
        }}
        
        @media (max-width: 768px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>INFORME FV ÃšLTIMOS 3 MESES</h1>
            <div class="nis">NIS: {metricas['nis']} | Cliente: {metricas['cliente']} | CategorÃ­a: {metricas['categoria']}</div>
        </div>
        
        <div class="main-layout">
            <div class="chart-container">
                <canvas id="chartBarras"></canvas>
            </div>
            
            <div class="sidebar">
                <div class="horarios-box">
                    <strong>Hs Resto:</strong> 05:00 Hs - 18:00 Hs<br>
                    <strong>Hs Punta:</strong> 18:00 Hs - 23:00 Hs<br>
                    <strong>Hs Valle:</strong> 23:00 Hs - 05:00 Hs
                </div>
                
                <div class="gauge-box">
                    <canvas id="chartGauge"></canvas>
                </div>
                
                <div class="tree-box">
                    <div class="tree-content">
                        {"<img src='" + tree_base64 + "' alt='Ãrbol'>" if tree_base64 else ""}
                        <div class="tree-value">{int(metricas['arboles'])}</div>
                    </div>
                    <div class="tree-label">Equivalente en Ã¡rboles</div>
                </div>
            </div>
        </div>
        
        <div class="factura-box">
            <div class="factura-titulo">Ãšltima factura considerada</div>
            <div class="factura-mes">{metricas['periodo']}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card-large consumo">
                <div class="metric-label-large">Consumo total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['consumo_acumulado']):,}</div>
            </div>
            <div class="metric-card-large generacion">
                <div class="metric-label-large">GeneraciÃ³n FV total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['generacion_acumulada']):,}</div>
            </div>
            <div class="metric-card-large ahorro">
                <div class="metric-label-large">Ahorro acumulado en $</div>
                <div class="metric-value-large">${int(metricas['ahorro_acumulado']):,}</div>
            </div>
        </div>
        
        <div class="footer">
            {"<img src='" + logo_base64 + "' alt='Nuevas EnergÃ­as'>" if logo_base64 else ""}
            <div class="footer-text">
                Fecha de la Ãºltima actualizaciÃ³n: {metricas['periodo']}<br>
                Este informe se genera automÃ¡ticamente
            </div>
        </div>
    </div>
    
    <script>
        // GrÃ¡fico 1: Barras Apiladas + LÃ­nea
        const ctxBarras = document.getElementById('chartBarras').getContext('2d');
        new Chart(ctxBarras, {{
            type: 'bar',
            data: {{
                labels: {labels_json},
                datasets: [
                    {{
                        label: 'Consumo hs resto [kWh]',
                        data: {resto_json},
                        backgroundColor: '#D32F2F',
                        stack: 'consumo',
                        order: 2
                    }},
                    {{
                        label: 'Consumo hs punta [kWh]',
                        data: {punta_json},
                        backgroundColor: '#FF9800',
                        stack: 'consumo',
                        order: 2
                    }},
                    {{
                        label: 'Consumo hs valle [kWh]',
                        data: {valle_json},
                        backgroundColor: '#757575',
                        stack: 'consumo',
                        order: 2
                    }},
                    {{
                        label: 'GeneraciÃ³n FV [kWh]',
                        type: 'line',
                        data: {generacion_json},
                        borderColor: '#000000',
                        backgroundColor: 'rgba(0,0,0,0)',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 4,
                        pointBackgroundColor: '#000000',
                        tension: 0.1,
                        order: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            font: {{ size: 11 }},
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + ' kWh';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: true,
                        grid: {{ display: false }}
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'GeneraciÃ³n y Consumo en kWh'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // GrÃ¡fico 2: Gauge COâ‚‚
        const ctxGauge = document.getElementById('chartGauge').getContext('2d');
        new Chart(ctxGauge, {{
            type: 'doughnut',
            data: {{
                datasets: [{{
                    data: [{co2_value}, {co2_max - co2_value}],
                    backgroundColor: ['#4285F4', '#E0E0E0'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ enabled: false }}
                }}
            }},
            plugins: [{{
                afterDraw: function(chart) {{
                    const ctx = chart.ctx;
                    const width = chart.width;
                    const height = chart.height;
                    
                    ctx.restore();
                    ctx.font = 'bold 28px Arial';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#000';
                    ctx.textAlign = 'center';
                    
                    const text = '{co2_value:,}'.replace(/,/g, '.');
                    ctx.fillText(text, width / 2, height / 2 - 10);
                    
                    ctx.font = '12px Arial';
                    ctx.fillStyle = '#666';
                    ctx.fillText('kg CO2e evitados', width / 2, height / 2 + 20);
                    
                    ctx.save();
                }}
            }}]
        }});
    </script>
</body>
</html>
"""
    
    return html
    """Genera el HTML del informe estilo Looker Studio."""
    
    logo_base64 = logo_to_base64()
    
    # Convertir imagen de Ã¡rbol a base64
    import base64
    tree_path = Path(__file__).parent / "tree_icon.png"
    tree_base64 = ""
    if tree_path.exists():
        with open(tree_path, "rb") as f:
            tree_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
    # Preparar URLs de QuickChart
    import json
    import urllib.parse
    
    # GRÃFICO 1: Barras Apiladas + LÃ­nea (estilo Looker)
    # QuickChart requiere configuraciÃ³n especÃ­fica para charts mixtos
    chart1_config = {
        "type": "bar",
        "data": {
            "labels": metricas['historico_labels'],
            "datasets": [
                {
                    "label": "Consumo hs resto [kWh]",
                    "data": metricas['historico_resto'],
                    "backgroundColor": "#D32F2F",
                    "stack": "consumo"
                },
                {
                    "label": "Consumo hs punta [kWh]",
                    "data": metricas['historico_punta'],
                    "backgroundColor": "#FF9800",
                    "stack": "consumo"
                },
                {
                    "label": "Consumo hs valle [kWh]",
                    "data": metricas['historico_valle'],
                    "backgroundColor": "#757575",
                    "stack": "consumo"
                },
                {
                    "label": "GeneraciÃ³n FV [kWh]",
                    "type": "line",
                    "data": metricas['historico_generacion'],
                    "borderColor": "#000000",
                    "backgroundColor": "rgba(0,0,0,0)",
                    "borderWidth": 2,
                    "fill": False,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#000000"
                }
            ]
        },
        "options": {
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"fontSize": 10}
                }
            },
            "scales": {
                "x": {
                    "stacked": True
                },
                "y": {
                    "stacked": True,
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "GeneraciÃ³n y Consumo en kWh"
                    }
                }
            }
        }
    }
    
    # GRÃFICO 2: Gauge semicircular para COâ‚‚
    # QuickChart tiene support para radialGauge
    co2_max = 5000  # Escala mÃ¡xima del gauge
    co2_percent = min((metricas['co2_evitado'] / co2_max) * 100, 100)
    
    chart2_config = {
        "type": "radialGauge",
        "data": {
            "datasets": [{
                "data": [co2_percent],
                "backgroundColor": "#4285F4"  # Azul como Looker
            }]
        },
        "options": {
            "trackColor": "#E0E0E0",
            "centerPercentage": 80,
            "centerArea": {
                "text": f"{int(metricas['co2_evitado']):,}",
                "fontSize": 28,
                "fontFamily": "Arial",
                "fontColor": "#000"
            }
        }
    }
    
    # Generar URLs
    base_url = "https://quickchart.io/chart"
    chart1_url = f"{base_url}?c={urllib.parse.quote(json.dumps(chart1_config))}&width=700&height=400&devicePixelRatio=2"
    chart2_url = f"{base_url}?c={urllib.parse.quote(json.dumps(chart2_config))}&width=300&height=200&devicePixelRatio=2"
    
    # HTML con diseÃ±o estilo Looker
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe FV - {metricas['cliente']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, 'Helvetica Neue', sans-serif;
            background: #C5D5CB;  /* Verde grisÃ¡ceo como Looker */
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #C5D5CB;
        }}
        
        /* HEADER */
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin-bottom: 10px;
        }}
        
        .header .nis {{
            font-size: 14px;
            color: #333;
            margin-bottom: 5px;
        }}
        
        /* LAYOUT PRINCIPAL */
        .main-layout {{
            display: grid;
            grid-template-columns: 7fr 3fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-container {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
        
        .chart-container img {{
            width: 100%;
            height: auto;
        }}
        
        /* SIDEBAR DERECHA */
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .horarios-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
        }}
        
        .gauge-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .gauge-box img {{
            width: 100%;
            max-width: 250px;
            margin: 0 auto;
        }}
        
        .gauge-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .tree-box {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .tree-box img {{
            width: 120px;
            height: auto;
            margin-bottom: 10px;
        }}
        
        .tree-value {{
            font-size: 32px;
            font-weight: bold;
            color: #000;
        }}
        
        .tree-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        /* ÃšLTIMA FACTURA */
        .factura-box {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .factura-titulo {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .factura-mes {{
            font-size: 24px;
            font-weight: bold;
            color: #000;
        }}
        
        /* TARJETAS GRANDES */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric-card-large {{
            padding: 30px 20px;
            border-radius: 4px;
            text-align: center;
            color: white;
        }}
        
        .metric-card-large.consumo {{
            background: #D32F2F;  /* Rojo */
        }}
        
        .metric-card-large.generacion {{
            background: #FFA726;  /* Naranja/Amarillo */
        }}
        
        .metric-card-large.ahorro {{
            background: #66BB6A;  /* Verde */
        }}
        
        .metric-label-large {{
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.95;
        }}
        
        .metric-value-large {{
            font-size: 36px;
            font-weight: bold;
        }}
        
        /* FOOTER */
        .footer {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 4px;
        }}
        
        .footer img {{
            max-width: 200px;
            height: auto;
        }}
        
        .footer-text {{
            font-size: 11px;
            color: #666;
            margin-top: 10px;
        }}
        
        @media (max-width: 768px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>INFORME FV ÃšLTIMOS 3 MESES</h1>
            <div class="nis">NIS: {metricas['nis']} | Cliente: {metricas['cliente']} | CategorÃ­a: {metricas['categoria']}</div>
        </div>
        
        <!-- LAYOUT PRINCIPAL -->
        <div class="main-layout">
            <!-- GRÃFICO PRINCIPAL -->
            <div class="chart-container">
                <img src="{chart1_url}" alt="GrÃ¡fico de Consumo y GeneraciÃ³n">
            </div>
            
            <!-- SIDEBAR DERECHA -->
            <div class="sidebar">
                <!-- HORARIOS -->
                <div class="horarios-box">
                    <strong>Hs Resto:</strong> 05:00 Hs - 18:00 Hs<br>
                    <strong>Hs Punta:</strong> 18:00 Hs - 23:00 Hs<br>
                    <strong>Hs Valle:</strong> 23:00 Hs - 05:00 Hs
                </div>
                
                <!-- GAUGE COâ‚‚ -->
                <div class="gauge-box">
                    <img src="{chart2_url}" alt="COâ‚‚ Evitado">
                    <div class="gauge-label">kg CO2e evitados</div>
                </div>
                
                <!-- ÃRBOL -->
                <div class="tree-box">
                    {"<img src='" + tree_base64 + "' alt='Ãrbol'>" if tree_base64 else ""}
                    <div class="tree-value">{int(metricas['arboles'])}</div>
                    <div class="tree-label">Equivalente en Ã¡rboles</div>
                </div>
            </div>
        </div>
        
        <!-- ÃšLTIMA FACTURA -->
        <div class="factura-box">
            <div class="factura-titulo">Ãšltima factura considerada</div>
            <div class="factura-mes">{metricas['periodo']}</div>
        </div>
        
        <!-- TARJETAS GRANDES -->
        <div class="metrics-grid">
            <div class="metric-card-large consumo">
                <div class="metric-label-large">Consumo total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['consumo_acumulado']):,}</div>
            </div>
            <div class="metric-card-large generacion">
                <div class="metric-label-large">GeneraciÃ³n FV total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['generacion_acumulada']):,}</div>
            </div>
            <div class="metric-card-large ahorro">
                <div class="metric-label-large">Ahorro acumulado en $</div>
                <div class="metric-value-large">${int(metricas['ahorro_acumulado']):,}</div>
            </div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            {"<img src='" + logo_base64 + "' alt='Nuevas EnergÃ­as'>" if logo_base64 else ""}
            <div class="footer-text">
                Fecha de la Ãºltima actualizaciÃ³n: {metricas['periodo']}<br>
                Este informe se genera automÃ¡ticamente
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html


# ================================================
# FUNCIÃ“N PRINCIPAL
# ================================================

def generar_todos_los_informes(output_dir=None):
    """Genera informes HTML para todos los NIS registrados."""
    import os
    print('='*70)
    print('GENERADOR DE INFORMES MENSUALES')
    print('='*70)
    print()
    
    # Crear carpeta de salida
    if not output_dir:
        fecha_hoy = datetime.now()
        output_dir = BASE_DIR / f'Informes_{fecha_hoy.month:02d}_{fecha_hoy.year}'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    print(f'Carpeta de salida: {output_dir}')
    print()
    
    # Leer datos
    datos = leer_datos_sheets()
    if not datos:
        print('ERROR: No se pudieron leer los datos de Google Sheets')
        return
    
    print(f'Leidos {len(datos)} registros')
    print()
    
    # Procesar cada NIS
    nis_list = list(NIS_NOMBRES.keys())
    total = len(nis_list)
    informes_generados = []
    
    for i, nis in enumerate(nis_list, 1):
        nombre_cliente = NIS_NOMBRES[nis]
        print(f'[{i}/{total}] Procesando {nombre_cliente} (NIS: {nis})')
        
        metricas = calcular_metricas_nis(datos, nis)
        
        if not metricas:
            print(f'  ADVERTENCIA: No hay datos para NIS {nis}')
            continue
        
        html = generar_html_informe(metricas).strip()
        
        # Guardar HTML
        filename = f'informe_{nis}_{nombre_cliente.replace(" ", "_")}.html'
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Registrar para GitHub
        informes_generados.append({
            'nis': nis,
            'cliente': nombre_cliente,
            'periodo': metricas['periodo'],
            'filepath': filepath
        })
        
        print(f'  Guardado: {filename}')
    
    print()
    
    # Publicar en GitHub si hay informes
    if informes_generados:
        publicar_en_github(informes_generados)
    
    print('='*70)
    print('PROCESO COMPLETADO')
    print(f'   Informes generados: {len(informes_generados)}')
    print(f'   Carpeta local: {output_dir}')
    print('='*70)


if __name__ == '__main__':
    generar_todos_los_informes()

