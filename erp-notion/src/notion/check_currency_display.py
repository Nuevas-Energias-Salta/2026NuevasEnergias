"""
Script para verificar y ajustar el formato para que muestre $ en lugar de ARS
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
    print("🔍 Verificando formato actual...\n")
    
    url = f"{BASE_URL}/databases/{CXC_DB_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code == 200:
        db = res.json()
        props = db.get("properties", {})
        
        monto = props.get("Monto", {})
        if monto.get("type") == "number":
            format_type = monto.get("number", {}).get("format")
            print(f"Formato actual de 'Monto': {format_type}")
        
        print("\n" + "=" * 60)
        print("📋 FORMATOS DISPONIBLES EN NOTION:")
        print("=" * 60)
        print("• 'number' → 3000")
        print("• 'dollar' → $3,000.00 (USD con coma y punto)")
        print("• 'argentine_peso' → $3.000,00 o ARS 3.000,00")
        print("\n💡 El formato 'argentine_peso' DEBERÍA mostrar '$'")
        print("   pero a veces Notion muestra 'ARS' según tu configuración.")
        print("\n⚠️ LIMITACIÓN DE NOTION:")
        print("   No hay control directo sobre si muestra '$' o 'ARS'")
        print("   Esto depende de:")
        print("   1. Tu configuración de idioma/región en Notion")
        print("   2. El navegador que uses")
        print("   3. La versión de Notion")
        print("=" * 60)
        
        print("\n💡 SOLUCIÓN:")
        print("=" * 60)
        print("Si ves 'ARS 3.000,00' y querés '$ 3.000,00':")
        print("\n1. En Notion, ve a Settings & Members")
        print("2. My settings → Language & region")
        print("3. Asegúrate que:")
        print("   - Language: Español")
        print("   - Region: Argentina o Latinoamérica")
        print("   - Number format: 1.234.567,89")
        print("\n4. Guardá y refrescá la página")
        print("=" * 60)
    else:
        print(f"❌ Error: {res.status_code}")

if __name__ == "__main__":
    check_current_format()
