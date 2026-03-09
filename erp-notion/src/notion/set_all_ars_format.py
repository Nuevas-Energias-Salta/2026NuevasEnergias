"""
Script COMPLETO para actualizar TODAS las columnas de monto a formato ARS
en TODAS las bases de datos del ERP
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

config.NOTION_TOKEN

# IDs de todas las bases de datos
DATABASES = {
    "Proyectos/Obras": "2e0c81c3-5804-8159-b677-fd8b76761e2f",
    "Cuentas por Cobrar": "2e0c81c3-5804-815a-8755-f4f254257f6a",
    "Cuentas por Pagar": "2e0c81c3-5804-8123-b1ae-d9b3579e0410",
    "Registro de Cobros": "2e0c81c3-5804-8123-985f-d8f25f8da8d4",
    "Registro de Pagos": "2e0c81c3-5804-81a0-bb7c-de1c31cf87a0",
    "Resumen CxC": None,  # Se buscará dinámicamente
    "Resumen CxP": None   # Se buscará dinámicamente
}

config.get_notion_headers()",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

config.NOTION_BASE_URL

# Columnas de monto por base de datos
MONEY_COLUMNS = {
    "Proyectos/Obras": ["Monto Contrato", "Presupuesto", "Costo Real"],
    "Cuentas por Cobrar": ["Monto"],
    "Cuentas por Pagar": ["Monto"],
    "Registro de Cobros": ["Monto"],
    "Registro de Pagos": ["Monto"],
    "Resumen CxC": ["Monto Total", "Monto Cobrado", "Saldo Pendiente"],
    "Resumen CxP": ["Monto Total", "Monto Pagado", "Saldo Pendiente"]
}

def find_database_by_name(name):
    """Busca una base de datos por nombre"""
    url = f"{BASE_URL}/search"
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
                    return result["id"]
        return None
    except:
        return None

def update_database_money_columns(db_id, db_name, column_names):
    """Actualiza las columnas de monto de una base de datos"""
    print(f"\n📊 {db_name}")
    print("  " + "=" * 50)
    
    url = f"{BASE_URL}/databases/{db_id}"
    
    # Obtener estructura actual
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"  ❌ Error obteniendo estructura: {res.status_code}")
            return 0
        
        db = res.json()
        properties = db.get("properties", {})
        
        # Preparar actualizaciones
        updates = {}
        updated_count = 0
        
        for col_name in column_names:
            if col_name in properties:
                prop = properties[col_name]
                prop_type = prop.get("type")
                
                if prop_type == "number":
                    # Actualizar solo si no tiene formato ARS
                    current_format = prop.get("number", {}).get("format")
                    if current_format != "argentine_peso":
                        updates[col_name] = {
                            "number": {"format": "argentine_peso"}
                        }
                        print(f"  ✓ {col_name}: actualizando a ARS")
                        updated_count += 1
                    else:
                        print(f"  ✓ {col_name}: ya tiene formato ARS")
                elif prop_type == "formula":
                    print(f"  ℹ️ {col_name}: es fórmula (hereda formato)")
                elif prop_type == "rollup":
                    print(f"  ℹ️ {col_name}: es rollup (hereda formato)")
                else:
                    print(f"  ⚠️ {col_name}: tipo {prop_type} no soportado")
            else:
                print(f"  ⚠️ {col_name}: no encontrada")
        
        # Aplicar actualizaciones si hay
        if updates:
            payload = {"properties": updates}
            res = requests.patch(url, headers=HEADERS, json=payload)
            if res.status_code == 200:
                print(f"  ✅ {updated_count} columnas actualizadas")
            else:
                print(f"  ❌ Error actualizando: {res.status_code}")
                return 0
        elif updated_count == 0:
            print(f"  ✓ Todas las columnas ya tienen formato correcto")
        
        return updated_count
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return 0

def main():
    print("=" * 60)
    print("💰 ACTUALIZANDO FORMATO ARS EN TODO EL ERP")
    print("=" * 60)
    
    # Buscar bases de datos que no tienen ID fijo
    print("\n🔍 Buscando bases de datos...")
    for db_name in ["Resumen CxC", "Resumen CxP"]:
        if db_name in DATABASES and DATABASES[db_name] is None:
            db_id = find_database_by_name(db_name)
            if db_id:
                DATABASES[db_name] = db_id
                print(f"  ✓ {db_name} encontrada")
            else:
                print(f"  ⚠️ {db_name} no encontrada")
    
    # Actualizar cada base de datos
    total_updated = 0
    
    for db_name, db_id in DATABASES.items():
        if db_id and db_name in MONEY_COLUMNS:
            columns = MONEY_COLUMNS[db_name]
            count = update_database_money_columns(db_id, db_name, columns)
            total_updated += count
    
    print("\n" + "=" * 60)
    print("✨ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"  Total columnas actualizadas: {total_updated}")
    print("\n💡 IMPORTANTE:")
    print("  - Refrescá Notion (F5) para ver los cambios")
    print("  - Las fórmulas y rollups heredan el formato automáticamente")
    print("  - Si 'Saldo Pendiente' no muestra ARS, es porque 'Monto'")
    print("    y 'Monto Cobrado' ahora sí lo tienen y se propagará")
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
