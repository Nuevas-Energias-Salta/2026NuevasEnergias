import os

file_path = 'cargador_universal_gui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Payment Methods
content = content.replace('"Visa Macro"', '"T VISA MACRO"')
content = content.replace('"Visa Galicia"', '"T VISA GALICIA"')
content = content.replace('"Visa BBVA"', '"T VISA BBVA"')

# Fix Monto Dolares Column Logic
old_props = """            props = {
                "Factura n°": {"title": [{"text": {"content": factura_n}}]},
                "Monto": {"number": item['monto']},
                "Fecha Factura": {"date": {"start": fecha_iso}},
                "Estado": {"select": {"name": "Pendiente"}},
                "Concepto": {"select": {"name": "Tarjeta de Crédito"}},
                "Categoría": {"select": {"name": "Servicios"}},
                "Método Pago": {"multi_select": [{"name": metodo_nombre}]}
            }"""

new_props = """            # Preparar montos según moneda (Columna dual en DB)
            monto_props = {}
            if item.get('moneda') == 'USD':
                monto_props["Monto Dolares"] = {"number": item['monto']}
                monto_props["Monto"] = {"number": 0}
            else:
                monto_props["Monto"] = {"number": item['monto']}

            props = {
                "Factura n°": {"title": [{"text": {"content": factura_n}}]},
                "Fecha Factura": {"date": {"start": fecha_iso}},
                "Estado": {"select": {"name": "Pendiente"}},
                "Concepto": {"select": {"name": "Tarjeta de Crédito"}},
                "Categoría": {"select": {"name": "Servicios"}},
                "Método Pago": {"multi_select": [{"name": metodo_nombre}]},
                **monto_props
            }"""

if old_props in content:
    content = content.replace(old_props, new_props)
    print("Monto props updated successfully.")
else:
    # Try even smaller chunks if exact match fails
    content = content.replace('"Monto": {"number": item[\'monto\']},', '')
    print("Fallback simple replace tried.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fix applied.")
