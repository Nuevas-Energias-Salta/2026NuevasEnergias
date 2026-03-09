# -*- coding: utf-8 -*-
"""
Herramienta para mapear plantas Growatt a NIS de EDESA
Permite verificar y ajustar el mapeo uno por uno
"""

import pandas as pd
from pathlib import Path
import sys

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent / "edesa_facturas" / "edesa_facturas"))

from nis_nombres import NIS_NOMBRES, LISTA_NIS_OFICIAL

def cargar_datos_growatt():
    """Carga los datos de generación de Growatt."""
    csv_path = Path("growatt_generacion_mensual_202601.csv")
    
    if not csv_path.exists():
        print(f"ERROR: No se encontró {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    return df


def mostrar_plantas_y_nis():
    """Muestra las plantas Growatt y los NIS disponibles lado a lado."""
    
    df = cargar_datos_growatt()
    if df is None:
        return
    
    # Filtrar solo plantas con generación > 0
    plantas_activas = df[df['Generacion_Mensual_kWh'] > 0].sort_values('Generacion_Mensual_kWh', ascending=False)
    
    print("\n" + "=" * 100)
    print("MAPEO DE PLANTAS GROWATT A NIS EDESA")
    print("=" * 100 + "\n")
    
    print("PLANTAS GROWATT ACTIVAS (con generacion > 0):")
    print("-" * 100)
    print(f"{'#':<4} {'Planta Growatt':<35} {'Ciudad':<20} {'Gen (kWh)':<15}")
    print("-" * 100)
    
    for idx, (_, row) in enumerate(plantas_activas.iterrows(), 1):
        ciudad = str(row['City']) if pd.notna(row['City']) else "N/A"
        print(f"{idx:<4} {row['Plant Name']:<35} {ciudad:<20} {row['Generacion_Mensual_kWh']:>12.2f}")
    
    print("\n\n")
    
    print("NIS EDESA DISPONIBLES (26 clientes):")
    print("-" * 100)
    print(f"{'#':<4} {'NIS':<10} {'Nombre Cliente':<40}")
    print("-" * 100)
    
    for idx, nis in enumerate(LISTA_NIS_OFICIAL, 1):
        nombre = NIS_NOMBRES[nis]
        print(f"{idx:<4} {nis:<10} {nombre:<40}")
    
    print("\n" + "=" * 100 + "\n")


def generar_mapeo_sugerido():
    """Genera un mapeo sugerido basado en nombres similares."""
    
    df = cargar_datos_growatt()
    if df is None:
        return
    
    print("\n" + "=" * 100)
    print("MAPEO SUGERIDO (basado en similitud de nombres)")
    print("=" * 100 + "\n")
    
    # Mapeo manual basado en análisis de nombres
    mapeo_sugerido = {
        # Matches directos o muy claros
        "cendis": ("5238545", "Cendis", "MATCH DIRECTO"),
        "Robles": ("3011513", "Robles", "MATCH DIRECTO"),
        "Diagnostico Salta": ("4000202", "Diagnostico Salta", "MATCH DIRECTO"),
        "puntocorp": ("5346470", "Punto Corp", "MATCH DIRECTO"),
        "Etchart": ("5019237", "Etchart", "MATCH DIRECTO"),
        "Línea C": ("5272486", "Linea C", "MATCH DIRECTO"),
        "La Carolina": ("5214767", "La Carolina", "MATCH DIRECTO"),
        "Campo quijano": ("5068576", "Facundo Alvarado", "PROBABLE - ubicacion"),
        "tambo martorel": ("5213946", "Tambo Martorell", "MATCH DIRECTO"),
        "Animana": ("4000681", "O.Domingo-Animana", "PROBABLE - ubicacion"),
        "valle del colectivo": ("5211887", "O.Domingo-Colectivo", "PROBABLE - nombre"),
        "Arenosa": ("5346222", "O.Domingo-Arenosa", "MATCH DIRECTO"),
        "Elizaldejoaquin": ("5253775", "Joaquín Elizalde", "PROBABLE - apellido"),
        "Ivan Bv": ("5253773", "Ivan BV", "MATCH DIRECTO"),
        "Imac Lerma": ("5320074", "Imac-RdL", "PROBABLE - Rosario de Lerma"),
        "Imac Frontera": ("5352763", "Imac-RdelaF", "PROBABLE - Rosario de la Frontera"),
        "Farm. San Francisco": ("3092029", "Farmacia San Francisco", "MATCH DIRECTO"),
        "Hotel La Merced del Alto": ("5076619", "LaMerceddelAlto", "MATCH DIRECTO"),
        "martin lecuona": ("5076526", "Martín Lecuona", "MATCH DIRECTO"),
        "Claudia tolaba": ("3062898", "Tolaba", "PROBABLE - apellido"),
        "distribuidora maestro": ("5263215", "Distribuidora Maestro", "MATCH DIRECTO"),
        "fabrica forja": ("5296128", "Fabrica Forja", "MATCH DIRECTO"),
        "Cartoon Inversor 1": ("5251104", "Cartoon Inversor 1", "MATCH DIRECTO"),
        "Cartoon inversor 2": ("5251101", "Cartoon Inversor 2", "MATCH DIRECTO"),
        "Agustin Lanus": ("5238577", "Agustín Lanús", "MATCH DIRECTO"),
        "viñas en flor": ("5214767", "La Carolina", "REVISAR - puede ser otra"),
    }
    
    print(f"{'Planta Growatt':<35} {'NIS':<10} {'Cliente EDESA':<30} {'Confianza':<20}")
    print("-" * 100)
    
    for planta, (nis, cliente, confianza) in sorted(mapeo_sugerido.items()):
        print(f"{planta:<35} {nis:<10} {cliente:<30} {confianza:<20}")
    
    print("\n")
    print("LEYENDA:")
    print("  MATCH DIRECTO - Nombres idénticos o muy similares")
    print("  PROBABLE      - Match basado en apellido, ubicación o contexto")
    print("  REVISAR       - Requiere verificación manual")
    
    print("\n" + "=" * 100 + "\n")
    
    return mapeo_sugerido


def verificar_nis_sin_planta():
    """Identifica NIS que no tienen planta Growatt asociada."""
    
    df = cargar_datos_growatt()
    if df is None:
        return
    
    print("\n" + "=" * 100)
    print("NIS SIN PLANTA GROWATT IDENTIFICADA")
    print("=" * 100 + "\n")
    
    # Lista de NIS que ya tienen mapeo
    nis_mapeados = {
        "5238545", "3011513", "4000202", "5346470", "5019237", "5272486",
        "5214767", "5068576", "5213946", "4000681", "5211887", "5346222",
        "5253775", "5253773", "5320074", "5352763", "3092029", "5076619",
        "5076526", "3062898", "5263215", "5296128", "5251104", "5251101",
        "5238577"
    }
    
    print(f"{'NIS':<10} {'Cliente EDESA':<40} {'Acción Sugerida':<30}")
    print("-" * 100)
    
    for nis in LISTA_NIS_OFICIAL:
        if nis not in nis_mapeados:
            nombre = NIS_NOMBRES[nis]
            print(f"{nis:<10} {nombre:<40} {'Buscar planta o confirmar sin solar':<30}")
    
    print("\n" + "=" * 100 + "\n")


def generar_codigo_mapeo():
    """Genera el código Python para el mapeo actualizado."""
    
    print("\n" + "=" * 100)
    print("CODIGO PARA ACTUALIZAR growatt_integration.py")
    print("=" * 100 + "\n")
    
    print("""
# Mapeo de nombres de plantas Growatt a NIS
GROWATT_NIS_MAP = {
    # Matches directos verificados
    "cendis": "5238545",                    # Cendis
    "Robles": "3011513",                    # Robles
    "Diagnostico Salta": "4000202",         # Diagnostico Salta
    "puntocorp": "5346470",                 # Punto Corp
    "Etchart": "5019237",                   # Etchart
    "Línea C": "5272486",                   # Linea C
    "La Carolina": "5214767",               # La Carolina
    "distribuidora maestro": "5263215",     # Distribuidora Maestro
    "fabrica forja": "5296128",             # Fabrica Forja
    "Farm. San Francisco": "3092029",       # Farmacia San Francisco
    "martin lecuona": "5076526",            # Martín Lecuona
    "Hotel La Merced del Alto": "5076619",  # LaMerceddelAlto
    "Cartoon Inversor 1": "5251104",        # Cartoon Inversor 1
    "Cartoon inversor 2": "5251101",        # Cartoon Inversor 2
    "Ivan Bv": "5253773",                   # Ivan BV
    "Agustin Lanus": "5238577",             # Agustín Lanús
    
    # Matches probables (verificar)
    "Campo quijano": "5068576",             # Facundo Alvarado
    "tambo martorel": "5213946",            # Tambo Martorell
    "Animana": "4000681",                   # O.Domingo-Animana
    "valle del colectivo": "5211887",       # O.Domingo-Colectivo
    "Arenosa": "5346222",                   # O.Domingo-Arenosa
    "Elizaldejoaquin": "5253775",           # Joaquín Elizalde
    "Imac Lerma": "5320074",                # Imac-RdL
    "Imac Frontera": "5352763",             # Imac-RdelaF
    "Claudia tolaba": "3062898",            # Tolaba
    
    # Revisar estos casos especiales
    # "viñas en flor": "5214767",           # ¿La Carolina? (revisar)
}
""")
    
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    print("\n")
    print("=" * 100)
    print(" " * 30 + "HERRAMIENTA DE MAPEO GROWATT -> NIS")
    print("=" * 100)
    
    # Mostrar todas las secciones
    mostrar_plantas_y_nis()
    generar_mapeo_sugerido()
    verificar_nis_sin_planta()
    generar_codigo_mapeo()
    
    print("\nPROXIMOS PASOS:")
    print("-" * 100)
    print("1. Revisar el mapeo sugerido")
    print("2. Verificar los casos marcados como 'PROBABLE' o 'REVISAR'")
    print("3. Identificar plantas para NIS sin mapeo")
    print("4. Actualizar growatt_integration.py con el mapeo correcto")
    print("\n")
