"""
Script para inspeccionar la fórmula de Saldo Pendiente
y entender cómo muestra el símbolo $
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

import json

config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def inspect_saldo_pendiente():
    """Inspecciona la configuración de Saldo Pendiente"""
    print("🔍 Inspeccionando 'Saldo Pendiente' en CxC...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code == 200:
        db = res.json()
        props = db.get("properties", {})
        
        saldo = props.get("Saldo Pendiente", {})
        
        print("=" * 60)
        print("Configuración de 'Saldo Pendiente':")
        print("=" * 60)
        print(f"Tipo: {saldo.get('type')}")
        
        if saldo.get('type') == 'formula':
            formula = saldo.get('formula', {})
            print(f"\nFórmula completa:")
            print(json.dumps(formula, indent=2))
        
        print("\n" + "=" * 60)
        print("\n💡 Para replicar esto en otras columnas:")
        print("=" * 60)
        print("Necesitamos crear columnas de fórmula similares que:")
        print("1. Tomen el valor de 'Monto' u otra columna numérica")
        print("2. Lo formateen con el símbolo $ delante")
        print("3. Mantengan el formato de puntos (300.000)")
        print("=" * 60)
    else:
        print(f"❌ Error: {res.status_code}")

if __name__ == "__main__":
    inspect_saldo_pendiente()
    
    print("\n" + "=" * 60)
    print("📝 PREGUNTA:")
    print("=" * 60)
    print("¿Cómo querés que se creen las columnas con $?")
    print("\nOpción A:")
    print("  - Renombrar 'Monto' a 'Monto (número)'")
    print("  - Crear nueva columna 'Monto' como fórmula con $")
    print("\nOpción B:")
    print("  - Mantener 'Monto' como está")
    print("  - Crear 'Monto Formateado' con fórmula $")
    print("  - Ocultar columna 'Monto' original")
    print("=" * 60)
