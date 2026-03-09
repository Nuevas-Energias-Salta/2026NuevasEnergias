# -*- coding: utf-8 -*-
"""
Generador de Informes Mensuales
Crea informes HTML individuales por cada NIS con métricas completas
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime

# Agregar path para importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent / "edesa_facturas" / "edesa_facturas"))

from extractor_zzz import get_sheets_service, SHEET_ID_ZZZ, SHEET_TAB_ZZZ
from nis_nombres import NIS_NOMBRES

# ================================================
# CONFIGURACIÓN
# ================================================

# Factores de cálculo
FACTOR_CO2_KG_KWH = 0.45  # kg CO2 por kWh (red Argentina)
FACTOR_ARBOLES = 22  # kg CO2 que absorbe un árbol por año

# Rutas
BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "NE-LOGO_EES-Positivo.png"


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
            # Rellenar con vacío si faltan columnas
            row_extended = row + [""] * (len(headers) - len(row))
            data.append(dict(zip(headers, row_extended)))
        
        return data
    
    except Exception as e:
        print(f"Error leyendo datos de Sheets: {e}")
        return None


def parse_numeric(value):
    """Convierte strings con formato monetario o numérico a float."""
    if not value or value == "":
        return 0.0
    
    try:
        # Remover símbolos de moneda, espacios, y convertir coma a punto
        cleaned = str(value).replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(cleaned)
    except:
        return 0.0


def calcular_metricas_nis(datos, nis):
    """
    Calcula todas las métricas para un NIS específico.
    Retorna dict con datos del último mes, acumulados históricos, y datos para gráficos.
    """
    # Filtrar datos de este NIS
    registros_nis = [d for d in datos if str(d.get("NIS", "")).strip() == str(nis)]
    
    if not registros_nis:
        return None
    
    # Último registro (el más reciente está en la fila 2, primera en la lista)
    ultimo = registros_nis[0]
    
    # Extraer datos del último mes
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
            consumo_acumulado += parse_numeric(reg.get("Consumo [kWh]", 0))
            gen = parse_numeric(reg.get("Generacion FV [kWh]", 0))
            generacion_acumulada += gen
            
            # Ahorro = Generación * Tarifa Resto (aproximación)
            tarifa_resto = parse_numeric(reg.get("Tarifa resto", 0))
            ahorro_acumulado += gen * tarifa_resto
        except:
            pass
    
    # Impacto ambiental del último mes
    co2_evitado = generacion_fv * FACTOR_CO2_KG_KWH
    arboles_equivalente = co2_evitado / FACTOR_ARBOLES
    
    # Datos históricos para gráficos (últimos 3 meses - TRIMESTRAL)
    historico_labels = []
    historico_consumo = []
    historico_generacion = []
    historico_punta = []
    historico_valle = []
    historico_resto = []
    
    for reg in registros_nis[:3]:  # Últimos 3 meses (trimestral como Looker)
        try:
            fecha = reg.get("    Fecha ", "").strip()  # Nota: tiene espacios
            consumo = parse_numeric(reg.get("Consumo [kWh]", 0))
            gen = parse_numeric(reg.get("Generacion FV [kWh]", 0))
            punta = parse_numeric(reg.get("Consumo hs punta [kWh]", 0))
            valle = parse_numeric(reg.get("Consumo hs valle [kWh]", 0))
            resto = parse_numeric(reg.get("Consumo hs resto[kWh]", 0))
            
            historico_labels.append(fecha)
            historico_consumo.append(consumo)
            historico_generacion.append(gen)
            historico_punta.append(punta)
            historico_valle.append(valle)
            historico_resto.append(resto)
        except:
            pass
    
    # Invertir listas para que estén en orden cronológico (más antiguo → más reciente)
    historico_labels.reverse()
    historico_consumo.reverse()
    historico_generacion.reverse()
    historico_punta.reverse()
    historico_valle.reverse()
    historico_resto.reverse()
    
    # Invertir para que el más antiguo esté primero
    historico_labels.reverse()
    historico_consumo.reverse()
    historico_generacion.reverse()
    
    return {
        "cliente": ultimo.get("Cliente", "Cliente"),
        "nis": nis,
        "periodo": ultimo.get("    Fecha ", "").strip(),  # Nota: header con espacios
        "categoria": ultimo.get("Catergoria", ""),  # Nota: con error de ortografía en Sheets
        
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
        
        # Acumulados
        "consumo_acumulado": consumo_acumulado,
        "generacion_acumulada": generacion_acumulada,
        "ahorro_acumulado": ahorro_acumulado,
        
        # Datos para gráficos
        "historico_labels": historico_labels,
        "historico_consumo": historico_consumo,
        "historico_generacion": historico_generacion,
        "historico_punta": historico_punta,
        "historico_valle": historico_valle,
        "historico_resto": historico_resto,
    }



# ================================================
# GENERACIÓN DE HTML
# ================================================

    """Genera el HTML del informe estilo Looker Studio."""
    
    logo_base64 = logo_to_base64()
    
    # Convertir imagen de árbol a base64
    import base64
    tree_path = Path(__file__).parent / "tree_icon.png"
    tree_base64 = ""
    if tree_path.exists():
        with open(tree_path, "rb") as f:
            tree_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
    # Preparar URLs de QuickChart
    import json
    import urllib.parse
    
    # GRÁFICO 1: Barras Apiladas + Línea (estilo Looker)
    # Barras apiladas para consumo (Resto, Punta, Valle)
    # Línea superpuesta para Generación FV
    chart1_config = {
        "type": "bar",
        "data": {
            "labels": metricas['historico_labels'],
            "datasets": [
                {
                    "label": "Consumo hs resto [kWh]",
                    "data": metricas['historico_resto'],
                    "backgroundColor": "#D32F2F",  # Rojo
                    "stack": "Stack 0",
                    "type": "bar"
                },
                {
                    "label": "Consumo hs punta [kWh]",
                    "data": metricas['historico_punta'],
                    "backgroundColor": "#FF9800",  # Naranja
                    "stack": "Stack 0",
                    "type": "bar"
                },
                {
                    "label": "Consumo hs valle [kWh]",
                    "data": metricas['historico_valle'],
                    "backgroundColor": "#757575",  # Gris
                    "stack": "Stack 0",
                    "type": "bar"
                },
                {
                    "label": "Generación FV [kWh]",
                    "data": metricas['historico_generacion'],
                    "borderColor": "#000000",
                    "backgroundColor": "transparent",
                    "type": "line",
                    "fill": False,
                    "borderWidth": 2,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#000000",
                    "yAxisID": "y"
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"font": {"size": 10}}
                },
                "title": {"display": False}
            },
            "scales": {
                "x": {"stacked": True},
                "y": {
                    "stacked": True,
                    "beginAtZero": True,
                    "title": {"display": True, "text": "Generación y Consumo en kWh (promedio)"}
                }
            }
        }
    }
    
    # GRÁFICO 2: Gauge semicircular para CO₂
    # QuickChart tiene support para radialGauge
    co2_max = 5000  # Escala máxima del gauge
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
    
    # HTML con diseño estilo Looker
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
            background: #C5D5CB;  /* Verde grisáceo como Looker */
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
        
        /* ÚLTIMA FACTURA */
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
            <h1>INFORME FV ÚLTIMOS 3 MESES</h1>
            <div class="nis">NIS: {metricas['nis']}</div>
        </div>
        
        <!-- LAYOUT PRINCIPAL -->
        <div class="main-layout">
            <!-- GRÁFICO PRINCIPAL -->
            <div class="chart-container">
                <img src="{chart1_url}" alt="Gráfico de Consumo y Generación">
            </div>
            
            <!-- SIDEBAR DERECHA -->
            <div class="sidebar">
                <!-- HORARIOS -->
                <div class="horarios-box">
                    <strong>Hs Resto:</strong> 05:00 Hs - 18:00 Hs<br>
                    <strong>Hs Punta:</strong> 18:00 Hs - 23:00 Hs<br>
                    <strong>Hs Valle:</strong> 23:00 Hs - 05:00 Hs
                </div>
                
                <!-- GAUGE CO₂ -->
                <div class="gauge-box">
                    <img src="{chart2_url}" alt="CO₂ Evitado">
                    <div class="gauge-label">kg CO2e evitados</div>
                </div>
                
                <!-- ÁRBOL -->
                <div class="tree-box">
                    {"<img src='" + tree_base64 + "' alt='Árbol'>" if tree_base64 else ""}
                    <div class="tree-value">{int(metricas['arboles'])}</div>
                    <div class="tree-label">Equivalente en árboles</div>
                </div>
            </div>
        </div>
        
        <!-- ÚLTIMA FACTURA -->
        <div class="factura-box">
            <div class="factura-titulo">Última factura considerada</div>
            <div class="factura-mes">{metricas['periodo']}</div>
        </div>
        
        <!-- TARJETAS GRANDES -->
        <div class="metrics-grid">
            <div class="metric-card-large consumo">
                <div class="metric-label-large">Consumo total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['consumo_acumulado']):,}</div>
            </div>
            <div class="metric-card-large generacion">
                <div class="metric-label-large">Generación FV total acum. [kWh]</div>
                <div class="metric-value-large">{int(metricas['generacion_acumulada']):,}</div>
            </div>
            <div class="metric-card-large ahorro">
                <div class="metric-label-large">Ahorro acumulado en $</div>
                <div class="metric-value-large">${int(metricas['ahorro_acumulado']):,}</div>
            </div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            {"<img src='" + logo_base64 + "' alt='Nuevas Energías'>" if logo_base64 else ""}
            <div class="footer-text">
                Cliente: {metricas['cliente']} | Categoría: {metricas['categoria']}<br>
                Fecha de la última actualización: {metricas['periodo']}<br>
                Este informe se genera automáticamente
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html
    """Genera el HTML del informe para un cliente."""
    
    logo_base64 = logo_to_base64()
    
    # Preparar URLs de QuickChart (API que genera gráficos como imágenes)
    import json
    import urllib.parse
    
    # Gráfico 1: Evolución Mensual (Línea)
    chart1_config = {
        "type": "line",
        "data": {
            "labels": metricas['historico_labels'],
            "datasets": [{
                "label": "Consumo",
                "data": metricas['historico_consumo'],
                "borderColor": "#4facfe",
                "backgroundColor": "rgba(79, 172, 254, 0.1)",
                "fill": True
            }, {
                "label": "Generación FV",
                "data": metricas['historico_generacion'],
                "borderColor": "#fa709a",
                "backgroundColor": "rgba(250, 112, 154, 0.1)",
                "fill": True
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Evolución Mensual (kWh)",
                    "font": {"size": 16, "weight": "bold"}
                },
                "legend": {"position": "bottom"}
            },
            "scales": {
                "y": {"beginAtZero": True}
            }
        }
    }
    
    # Gráfico 2: Distribución (Donut)
    chart2_config = {
        "type": "doughnut",
        "data": {
            "labels": ["Punta", "Valle", "Resto"],
            "datasets": [{
                "data": [metricas['consumo_punta'], metricas['consumo_valle'], metricas['consumo_resto']],
                "backgroundColor": [
                    "rgba(79, 172, 254, 0.8)",
                    "rgba(67, 233, 123, 0.8)",
                    "rgba(250, 112, 154, 0.8)"
                ],
                "borderColor": ["#4facfe", "#43e97b", "#fa709a"],
                "borderWidth": 2
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Distribución Consumo del Mes",
                    "font": {"size": 14, "weight": "bold"}
                },
                "legend": {"position": "bottom"}
            }
        }
    }
    
    # Gráfico 3: Comparación (Barras)
    chart3_config = {
        "type": "bar",
        "data": {
            "labels": ["Mes Actual"],
            "datasets": [{
                "label": "Consumo Total (kWh)",
                "data": [metricas['consumo_total']],
                "backgroundColor": "rgba(79, 172, 254, 0.8)",
                "borderColor": "#4facfe",
                "borderWidth": 2
            }, {
                "label": "Generación FV (kWh)",
                "data": [metricas['generacion_fv']],
                "backgroundColor": "rgba(250, 112, 154, 0.8)",
                "borderColor": "#fa709a",
                "borderWidth": 2
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Consumo vs Generación - Mes Actual",
                    "font": {"size": 16, "weight": "bold"}
                },
                "legend": {"position": "bottom"}
            },
            "scales": {
                "y": {"beginAtZero": True}
            }
        }
    }
    
    # Generar URLs de QuickChart
    base_url = "https://quickchart.io/chart"
    chart1_url = f"{base_url}?c={urllib.parse.quote(json.dumps(chart1_config))}&width=600&height=300"
    chart2_url = f"{base_url}?c={urllib.parse.quote(json.dumps(chart2_config))}&width=300&height=300"
    chart3_url = f"{base_url}?c={urllib.parse.quote(json.dumps(chart3_config))}&width=600&height=300"
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe Mensual - {metricas['cliente']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #ff9a56 0%, #ffcb52 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .logo {{
            max-width: 250px;
            margin-bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 12px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 8px;
        }}
        
        .header .periodo {{
            font-size: 18px;
            opacity: 0.95;
            font-weight: 300;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .info-cliente {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            border-left: 4px solid #ff9a56;
        }}
        
        .info-cliente p {{
            margin: 8px 0;
            font-size: 15px;
        }}
        
        .info-cliente .label {{
            font-weight: 600;
            color: #495057;
        }}
        
        .seccion {{
            margin-bottom: 30px;
        }}
        
        .seccion-titulo {{
            font-size: 20px;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .seccion-titulo .icono {{
            font-size: 24px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #ff9a56 0%, #ffc266 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .metric-card.blue {{
            background: linear-gradient(135deg, #ffb366 0%, #ffe066 100%);
        }}
        
        .metric-card.green {{
            background: linear-gradient(135deg, #76b852 0%, #8DC26F 100%);
        }}
        
        .metric-card.orange {{
            background: linear-gradient(135deg, #ff9a56 0%, #ffcb52 100%);
        }}
        
        .metric-card.gray {{
            background: linear-gradient(135deg, #7c8690 0%, #98a5b0 100%);
        }}
        
        .metric-label {{
            font-size: 13px;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
        }}
        
        .metric-unit {{
            font-size: 14px;
            opacity: 0.9;
            margin-left: 4px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .chart-container img {{
            max-width: 100%;
            height: auto;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        
        @media (max-width: 768px) {{
            .chart-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #dee2e6;
        }}
        
        .footer strong {{
            color: #495057;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {"<img src='" + logo_base64 + "' alt='Nuevas Energías' class='logo'>" if logo_base64 else ""}
            <h1>📊 INFORME MENSUAL DE ENERGÍA</h1>
            <div class="periodo">Período: {metricas['periodo']}</div>
        </div>
        
        <div class="content">
            <div class="info-cliente">
                <p><span class="label">Cliente:</span> {metricas['cliente']}</p>
                <p><span class="label">NIS:</span> {metricas['nis']}</p>
                <p><span class="label">Categoría:</span> {metricas['categoria']}</p>
            </div>
            
            <!-- GRÁFICOS -->
            <div class="seccion">
                <h2 class="seccion-titulo">
                    <span class="icono">📊</span>
                    Visualización de Datos
                </h2>
                <div class="chart-grid">
                    <div class="chart-container">
                        <img src="{chart1_url}" alt="Gráfico de Evolución Mensual">
                    </div>
                    <div class="chart-container">
                        <img src="{chart2_url}" alt="Gráfico de Distribución">
                    </div>
                </div>
                <div class="chart-container">
                    <img src="{chart3_url}" alt="Gráfico de Comparación">
                </div>
            </div>
            
            <!-- CONSUMO ELÉCTRICO -->
            <div class="seccion">
                <h2 class="seccion-titulo">
                    <span class="icono">⚡</span>
                    Consumo Eléctrico del Mes
                </h2>
                <div class="grid">
                    <div class="metric-card blue">
                        <div class="metric-label">Punta</div>
                        <div class="metric-value">{metricas['consumo_punta']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                    <div class="metric-card blue">
                        <div class="metric-label">Valle</div>
                        <div class="metric-value">{metricas['consumo_valle']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                    <div class="metric-card blue">
                        <div class="metric-label">Resto</div>
                        <div class="metric-value">{metricas['consumo_resto']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                    <div class="metric-card gray">
                        <div class="metric-label">TOTAL</div>
                        <div class="metric-value">{metricas['consumo_total']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                </div>
            </div>
            
            <!-- GENERACIÓN SOLAR -->
            <div class="seccion">
                <h2 class="seccion-titulo">
                    <span class="icono">☀️</span>
                    Generación Solar
                </h2>
                <div class="grid">
                    <div class="metric-card orange">
                        <div class="metric-label">Generación FV</div>
                        <div class="metric-value">{metricas['generacion_fv']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                </div>
            </div>
            
            <!-- IMPACTO AMBIENTAL -->
            <div class="seccion">
                <h2 class="seccion-titulo">
                    <span class="icono">🌱</span>
                    Impacto Ambiental del Mes
                </h2>
                <div class="grid">
                    <div class="metric-card green">
                        <div class="metric-label">CO₂ Evitado</div>
                        <div class="metric-value">{metricas['co2_evitado']:.1f}<span class="metric-unit">kg</span></div>
                    </div>
                    <div class="metric-card green">
                        <div class="metric-label">Equivalente en Árboles</div>
                        <div class="metric-value">{metricas['arboles']:.1f}<span class="metric-unit">árboles</span></div>
                    </div>
                </div>
            </div>
            
            <!-- ACUMULADOS -->
            <div class="seccion">
                <h2 class="seccion-titulo">
                    <span class="icono">📈</span>
                    Acumulado Histórico
                </h2>
                <div class="grid">
                    <div class="metric-card gray">
                        <div class="metric-label">Consumo Total</div>
                        <div class="metric-value">{metricas['consumo_acumulado']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                    <div class="metric-card orange">
                        <div class="metric-label">Generación Total</div>
                        <div class="metric-value">{metricas['generacion_acumulada']:.0f}<span class="metric-unit">kWh</span></div>
                    </div>
                    <div class="metric-card green">
                        <div class="metric-label">Ahorro Total</div>
                        <div class="metric-value">${metricas['ahorro_acumulado']:,.0f}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Nuevas Energías</strong> - Eficiente es Sustentable</p>
            <p>Este informe se genera automáticamente desde nuestro sistema de gestión.</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html



# ================================================
# FUNCIÓN PRINCIPAL
# ================================================

def generar_todos_los_informes(output_dir=None):
    """
    Genera informes HTML para todos los NIS registrados.
    
    Args:
        output_dir: Carpeta donde guardar los HTMLs. Si es None, usa Informes_MMYYYY
    """
    print("=" * 70)
    print("GENERADOR DE INFORMES MENSUALES")
    print("=" * 70)
    print()
    
    # Crear carpeta de salida
    if output_dir is None:
        fecha_actual = datetime.now()
        output_dir = BASE_DIR / f"Informes_{fecha_actual.strftime('%m_%Y')}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    print(f"Carpeta de salida: {output_dir}")
    print()
    
    # Leer datos de Sheets
    print("Leyendo datos de Google Sheets...")
    datos = leer_datos_sheets()
    
    if not datos:
        print("Error: No se pudieron leer los datos")
        return False
    
    print(f"Leidos {len(datos)} registros")
    print()
    
    # Generar informe por cada NIS
    nis_procesados = set()
    informes_generados = 0
    
    for nis, nombre in NIS_NOMBRES.items():
        if nis in nis_procesados:
            continue
        
        print(f"[{informes_generados + 1}/{len(NIS_NOMBRES)}] Procesando {nombre} (NIS: {nis})")
        
        metricas = calcular_metricas_nis(datos, nis)
        
        if not metricas:
            print(f"  Sin datos para este NIS")
            continue
        
        # Generar HTML
        html = generar_html_informe(metricas)
        
        # Guardar archivo
        nombre_archivo = f"informe_{nis}_{metricas['cliente'].replace(' ', '_')}.html"
        ruta_archivo = output_dir / nombre_archivo
        
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"  Guardado: {nombre_archivo}")
        
        nis_procesados.add(nis)
        informes_generados += 1
    
    print()
    print("=" * 70)
    print(f"PROCESO COMPLETADO")
    print(f"   Informes generados: {informes_generados}")
    print(f"   Carpeta: {output_dir}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    generar_todos_los_informes()
