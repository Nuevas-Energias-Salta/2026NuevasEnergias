# -*- coding: utf-8 -*-
"""
Script de prueba para 3 NIS para verificar la extracción y llenado del Excel.
"""

import sys
import os
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

# Importar funciones
from descargar_facturas_MEJORADO import leer_planilla, descargar_factura, subir_a_drive
from extractor_zzz import procesar_y_subir_factura
import re

def main():
    print("Iniciando prueba con 3 NIS...")
    df = leer_planilla()
    
    # Tomamos solo los 3 primeros NIS
    df = df.head(3)
    
    total = len(df)
    print(f"📋 Clientes seleccionados para la prueba: {total}")
    
    for i, row in df.iterrows():
        nis = re.sub(r"\D", "", str(row["NIS"]))
        cliente = str(row["Cliente"])
        
        if not nis: continue
        
        print(f"\n📥 [{i+1}/{total}] Descargando EDESA para: {cliente} (NIS {nis})...")
        tmp = BASE_DIR / f"tmp_{nis}"
        tmp.mkdir(exist_ok=True)
        
        try:
            ok, err = descargar_factura(nis, str(tmp))
            if ok:
                pdfs = list(tmp.glob("*.pdf"))
                if pdfs:
                    pdf = pdfs[0]
                    print(f"  ☁️ Subiendo a Drive...")
                    # Comentado para no llenar el Drive innecesariamente en la prueba
                    # subir_a_drive(pdf.name, str(pdf)) 
                    
                    print(f"  📊 Extrayendo datos y actualizando Sheets ZZZ...")
                    resultado = procesar_y_subir_factura(str(pdf))
                    if resultado:
                        print("  ✅ Exitoso. Si Growatt Generation dio 0, verifiquemos el log del Excel.")
            else:
                print(f"  ❌ Error: {err}")
        except Exception as e:
            print(f"  ⚠️ Fallo técnico: {e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            
    print("\n✅ Prueba de EDESA + Extractor finalizada.")
    print("Podemos revisar el Excel online para verificar estos 3 NIS.")

if __name__ == "__main__":
    main()
