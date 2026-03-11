# -*- coding: utf-8 -*-
"""
Motor de Detección de Oportunidades y Anomalías (Growth)
--------------------------------------------------------
Extrae métricas desde Google Sheets y ejecuta un motor de reglas 
para generar leads B2B/B2C y detectar problemas técnicos.
"""

import sys
import datetime
from pathlib import Path

# Configuración de rutas para importar módulos locales
BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(EDESA_DIR))

from extractor_zzz import get_sheets_service, SHEET_ID_ZZZ, SHEET_TAB_ZZZ

def parse_numeric(value):
    """Convierte strings con formato monetario o numérico a float."""
    if value is None or str(value).strip() == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).replace('$', '').replace(' ', '')
    try:
        if ',' in val_str and '.' in val_str:
            val_str = val_str.replace('.', '')
            val_str = val_str.replace(',', '.')
        elif ',' in val_str:
            val_str = val_str.replace(',', '.')
        return float(val_str)
    except:
        return 0.0

def leer_datos():
    """Lee todos los registros de la planilla ZZZ."""
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID_ZZZ,
            range=SHEET_TAB_ZZZ
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            return []
            
        headers = [h.strip() for h in values[0]]
        registros = []
        for row in values[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = row[i]
                else:
                    row_dict[header] = ""
            registros.append(row_dict)
            
        return registros
    except Exception as e:
        print(f"Error leyendo datos de Sheets: {e}")
        return []

def detectar_oportunidades(datos):
    """
    Analiza el historial de todos los clientes y extrae oportunidades 
    siguiendo las reglas de la Máquina de Growth.
    """
    print("Iniciando Motor de Detección de Oportunidades...")
    clientes_agrupados = {}
    
    # Agrupar datos por NIS
    for reg in datos:
        nis = str(reg.get("NIS", "")).strip()
        if not nis: continue
        if nis not in clientes_agrupados:
            clientes_agrupados[nis] = []
        clientes_agrupados[nis].append(reg)
        
    oportunidades = []
    mes_actual_num = datetime.datetime.now().month

    for nis, registros in clientes_agrupados.items():
        if not registros:
            continue
            
        ultimo = registros[0]
        cliente_nombre = ultimo.get("Cliente", "Desconocido")
        telefono = ultimo.get("Telefono", "")
        
        try:
            gen_actual = parse_numeric(ultimo.get("Generacion FV [kWh]", 0))
            cons_red_actual = parse_numeric(ultimo.get("Consumo [kWh]", 0))
            cons_punta = parse_numeric(ultimo.get("Consumo hs punta [kWh]", 0))
            cons_resto = parse_numeric(ultimo.get("Consumo hs resto[kWh]", 0))
            cons_valle = parse_numeric(ultimo.get("Consumo hs valle [kWh]", 0))
            inyeccion = parse_numeric(ultimo.get("Energia Inyectada [kWh]", 0))
            
            # --- REGLA O1: Oportunidad de BATERÍAS ---
            # Mucha inyección, pero sigue gastando mucho a la noche (Punta + Valle)
            # Aproximamos: si inyecta más de 50kWh y consume de red más de 100kWh de noche.
            if inyeccion > 50 and (cons_punta + cons_valle) > 100:
                oportunidades.append({
                    "NIS": nis,
                    "Cliente": cliente_nombre,
                    "Tipo": "Baterías / Backup",
                    "Motivo": f"Inyecta {inyeccion:,.0f}kWh pero consume {cons_punta+cons_valle:,.0f}kWh de red (punta+valle).",
                    "Prioridad": "ALTA"
                })
                
            # --- REGLA O2: Oportunidad de AMPLIACIÓN FV ---
            # Casi no inyecta (consume todo) y el consumo total es muy superior a la generación
            cons_total = cons_red_actual + gen_actual
            if cons_total > 0 and (gen_actual / cons_total) < 0.30 and inyeccion < 10 and gen_actual > 0:
                oportunidades.append({
                    "NIS": nis,
                    "Cliente": cliente_nombre,
                    "Tipo": "Ampliación Solar",
                    "Motivo": f"Sistema chico. Genera {gen_actual:,.0f}kWh pero consume en total {cons_total:,.0f}kWh.",
                    "Prioridad": "MEDIA"
                })

            # --- REGLA O3: Oportunidad CALEFACCIÓN SOLAR / CLIMATIZACIÓN ---
            # En meses de frío (Mar-Ago), ofrecer Termotanque Solar o Calefacción a los FV que consumen mucha red
            if 3 <= mes_actual_num <= 8 and cons_red_actual > 400:
                oportunidades.append({
                    "NIS": nis,
                    "Cliente": cliente_nombre,
                    "Tipo": "Cross-sell: Calefacción/ACS",
                    "Motivo": f"Alto consumo de red en invierno ({cons_red_actual:,.0f}kWh).",
                    "Prioridad": "MEDIA"
                })
                
            # --- REGLA A1: ANOMALÍA - Caída drástica de generación ---
            # Comparar el mes actual con el mes anterior
            if len(registros) >= 2:
                gen_anterior = parse_numeric(registros[1].get("Generacion FV [kWh]", 0))
                # Si cayó más del 40%
                if gen_anterior > 50 and gen_actual < (gen_anterior * 0.60):
                    oportunidades.append({
                        "NIS": nis,
                        "Cliente": cliente_nombre,
                        "Tipo": "Anomalía Técnica",
                        "Motivo": f"Producción solar cayó un {((gen_anterior-gen_actual)/gen_anterior)*100:.0f}% vs el mes pasado.",
                        "Prioridad": "URGENTE"
                    })
                    
        except Exception as e:
            print(f"Error procesando {nis}: {e}")
            
    return oportunidades

def exportar_oportunidades(oportunidades, ruta_salida):
    """Guarda las oportunidades en un archivo CSV simple."""
    if not oportunidades:
        print("No se detectaron nuevas oportunidades este ciclo.")
        return
        
    ruta = Path(ruta_salida)
    # Crear directorio si no existe
    ruta.parent.mkdir(parents=True, exist_ok=True)
    
    import csv
    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Prioridad", "Tipo", "Cliente", "NIS", "Motivo"])
        writer.writeheader()
        
        # Ordenar por prioridad (URGENTE, ALTA, MEDIA, BAJA)
        orden = {"URGENTE": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3}
        oportunidades.sort(key=lambda x: orden.get(x["Prioridad"], 4))
        
        for op in oportunidades:
            writer.writerow(op)
            
    print(f"✅ {len(oportunidades)} Oportunidades exportadas a: {ruta.name}")

if __name__ == "__main__":
    datos = leer_datos()
    if datos:
        ops = detectar_oportunidades(datos)
        hoy_str = datetime.datetime.now().strftime("%Y%m%d")
        ruta_csv = Path(__file__).parent / "github_pages" / f"oportunidades_comerciales_{hoy_str}.csv"
        exportar_oportunidades(ops, ruta_csv)
        
        print("\n--- RESUMEN DE OPORTUNIDADES DETECTADAS ---")
        for o in ops:
            print(f"[{o['Prioridad']}] {o['Tipo']} -> {o['Cliente']} : {o['Motivo']}")
