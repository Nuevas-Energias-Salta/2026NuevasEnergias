# -*- coding: utf-8 -*-
"""
Previsualizador de Email - Muestra cómo se verá el email que reciben los clientes
"""

from email_sender import crear_template_email
from pathlib import Path
import webbrowser

def generar_preview():
    """Genera un preview HTML del email y lo abre en el navegador."""
    
    # Datos de ejemplo
    nombre_cliente = "Juan Pérez"
    link_informe = "https://tu-usuario.github.io/zzz-informes/informe_3011513_Juan_Perez.html"
    periodo = "Febrero 2026"
    metricas = {
        'consumo_total': 1234,
        'generacion': 567,
        'ahorro_estimado': 45250
    }
    
    # Generar HTML
    html_content = crear_template_email(
        nombre_cliente=nombre_cliente,
        link_informe=link_informe,
        periodo=periodo,
        metricas=metricas
    )
    
    # Guardar en archivo temporal
    preview_file = Path(__file__).parent / "preview_email.html"
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Preview generado exitosamente!")
    print(f"📄 Archivo: {preview_file}")
    print("🌐 Abriendo en navegador...")
    
    # Abrir en navegador
    webbrowser.open(str(preview_file))
    
    print("\n💡 Este es el email que recibirán tus clientes.")
    print("   Puedes editar el template en email_sender.py")

if __name__ == "__main__":
    generar_preview()
