# -*- coding: utf-8 -*-
"""
Script de prueba para extraer datos de Growatt solo de 3 plantas.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

from edesa_facturas.edesa_facturas import growatt_integration

# Forzar el mapa a solo 3 plantas de prueba
growatt_integration.GROWATT_NIS_MAP = {
    "La Aurelia": "3025373", 
    "Etchart": "5019237",
    "Agustin Lanus": "5238577"
}

print("⚠️ ADVERTENCIA: Este script modificará el CSV de Growatt solo con 3 plantas para la prueba.")
print("Iniciando extracción automática de Growatt para 3 plantas...\n")

success = growatt_integration.extraer_datos_growatt_auto(
    periodo="mar 2026", 
    callback_log=print
)

if success:
    print("\n✅ Extracción de prueba finalizada correctamente. (Generación Growth probada para 3 NIS).")
    print("Por favor revisa el archivo 'growatt_generacion_mensual_202603.csv' y el Excel ZZZ.")
else:
    print("\n❌ Hubo un error en la extracción de prueba.")
