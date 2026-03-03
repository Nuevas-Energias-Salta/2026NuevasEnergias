"""
Script para verificar formatos de número disponibles en Notion
El formato argentino debería usar punto como separador de miles
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config


config.NOTION_TOKEN
CXC_DB_ID = "2e0c81c3-5804-815a-8755-f4f254257f6a"

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def check_current_format():
    """Verifica el formato actual"""
    print("🔍 Verificando formato actual de Saldo Pendiente...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            db = res.json()
            props = db.get("properties", {})
            
            saldo_prop = props.get("Saldo Pendiente", {})
            print(f"Tipo: {saldo_prop.get('type')}")
            
            if saldo_prop.get('type') == 'formula':
                formula_data = saldo_prop.get('formula', {})
                print(f"Formula expression: {formula_data.get('expression')}")
                print(f"Formula output: {formula_data}")
            
            print("\n" + "=" * 60)
            print("ℹ️ NOTA IMPORTANTE:")
            print("=" * 60)
            print("El formato 'argentine_peso' DEBE mostrar números como 300.000")
            print("(con punto como separador de miles).")
            print("\nSi ves 300,000 (con coma), puede ser por:")
            print("  1. Configuración de idioma de tu navegador")
            print("  2. Configuración regional de Notion")
            print("\n💡 SOLUCIÓN:")
            print("  1. Ve a Settings & Members en Notion")
            print("  2. My settings → Language & region")
            print("  3. Asegúrate que esté en 'Español (Latinoamérica)' o similar")
            print("=" * 60)
            
        else:
            print(f"❌ Error: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_current_format()
