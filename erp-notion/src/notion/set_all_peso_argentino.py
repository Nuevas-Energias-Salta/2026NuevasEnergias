"""
Script COMPLETO para configurar formato de pesos argentinos ($)
en TODAS las columnas de dinero del ERP de Notion
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

config.NOTION_TOKEN

# Todas las bases de datos del ERP
DATABASES = {
    "Proyectos/Obras": "2e0c81c3-5804-8159-b677-fd8b76761e2f",
    "Cuentas por Cobrar": "2e0c81c3-5804-815a-8755-f4f254257f6a",
    "Cuentas por Pagar": "2e0c81c3-5804-8123-b1ae-d9b3579e0410",
}

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

def get_all_number_columns(db_id):
    """Obtiene todas las columnas de tipo número de una base de datos"""
    url = f"{BASE_URL}/databases/{db_id}"
    
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            db = res.json()
            props = db.get("properties", {})
            
            number_cols = []
            for name, prop in props.items():
                if prop.get("type") == "number":
                    number_cols.append(name)
            
            return number_cols
        return []
    except:
        return []

def update_all_to_argentine_peso(db_id, db_name):
    """Actualiza TODAS las columnas de número a formato pesos argentinos ($)"""
    print(f"\n💰 {db_name}")
    print("  " + "=" * 50)
    
    # Obtener todas las columnas numéricas
    number_cols = get_all_number_columns(db_id)
    
    if not number_cols:
        print("  ⚠️ No se encontraron columnas numéricas")
        return 0
    
    print(f"  📊 Encontradas {len(number_cols)} columnas numéricas:")
    for col in number_cols:
        print(f"    • {col}")
    
    # Preparar actualización
    url = f"{BASE_URL}/databases/{db_id}"
    
    properties = {}
    for col in number_cols:
        properties[col] = {
            "number": {"format": "argentine_peso"}
        }
    
    payload = {"properties": properties}
    
    try:
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print(f"  ✅ {len(number_cols)} columnas actualizadas a formato $ (pesos argentinos)")
            return len(number_cols)
        else:
            print(f"  ❌ Error: {res.status_code}")
            print(f"     {res.text[:100]}")
            return 0
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return 0

def update_resumen_databases():
    """Actualiza las bases de datos de resumen (si existen)"""
    print("\n🔍 Buscando bases de datos de Resumen...")
    
    url = f"{BASE_URL}/search"
    total = 0
    
    for name in ["Resumen CxC", "Resumen CxP"]:
        payload = {
            "query": name,
            "filter": {"property": "object", "value": "database"}
        }
        
        try:
            res = requests.post(url, headers=HEADERS, json=payload)
            if res.status_code == 200:
                results = res.json().get("results", [])
                for result in results:
                    title = result.get("title", [{}])[0].get("text", {}).get("content", "")
                    if name in title:
                        db_id = result["id"]
                        count = update_all_to_argentine_peso(db_id, name)
                        total += count
                        break
        except:
            pass
    
    return total

def main():
    print("=" * 60)
    print("💵 CONFIGURANDO $ (PESOS ARGENTINOS) EN TODO EL ERP")
    print("=" * 60)
    print("\n⚠️ IMPORTANTE:")
    print("  El símbolo $ representa PESOS ARGENTINOS")
    print("  Formato: argentine_peso")
    print("  Ejemplo: $300.000 (con punto como separador de miles)")
    print("=" * 60)
    
    total_updated = 0
    
    # Actualizar bases principales
    for db_name, db_id in DATABASES.items():
        count = update_all_to_argentine_peso(db_id, db_name)
        total_updated += count
    
    # Actualizar bases de resumen
    count = update_resumen_databases()
    total_updated += count
    
    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"  Total columnas actualizadas: {total_updated}")
    print("\n💡 RESULTADO:")
    print("  ✓ Todas las columnas numéricas ahora usan formato $")
    print("  ✓ El símbolo $ representa PESOS ARGENTINOS")
    print("  ✓ Formato: $300.000 (punto como separador de miles)")
    print("\n📌 ACCIÓN REQUERIDA:")
    print("  1. Refrescá Notion completamente (F5 o Ctrl+R)")
    print("  2. Esperá 10 segundos a que recalcule las fórmulas")
    print("  3. Verificá que todas las columnas muestren el $")
    print("\n⚠️ SOBRE SALDO PENDIENTE:")
    print("  Es una fórmula, heredará el $ de 'Monto'")
    print("  Si no lo ves, puede ser una limitación de Notion")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

        traceback.print_exc()
