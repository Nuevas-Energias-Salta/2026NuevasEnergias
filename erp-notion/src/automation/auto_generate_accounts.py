"""
Script unificado para generar automáticamente CxC y CxP desde proyectos.
Ejecuta ambos procesos de forma secuencial con opciones de configuración.
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Importar configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

def print_header():
    print("=" * 70)
    print("🏗️  GENERACIÓN AUTOMÁTICA DE CUENTAS - SISTEMA ERP")
    print("=" * 70)
    print("\nEste script generará automáticamente:")
    print("   📤 Cuentas por Cobrar (CxC) desde proyectos")
    print("   📥 Cuentas por Pagar (CxP) desde proyectos")
    print("\n" + "=" * 70)

def get_user_choice():
    """Pregunta al usuario qué desea ejecutar"""
    print("\n¿Qué deseas ejecutar?")
    print("   1. Generar solo CxC (Cuentas por Cobrar)")
    print("   2. Generar solo CxP (Cuentas por Pagar)")
    print("   3. Generar ambas (CxC + CxP)")
    print("   4. Salir")
    
    while True:
        try:
            choice = input("\nElige una opción (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                return choice
            else:
                print("⚠️ Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\n\n❌ Operación cancelada por el usuario.")
            return "4"

def configure_cxc():
    """Configuración para generación de CxC"""
    print("\n" + "-" * 70)
    print("⚙️  CONFIGURACIÓN CxC")
    print("-" * 70)
    print("\n¿Cómo deseas generar las cuentas por cobrar?")
    print("   1. Pago único (1 cuenta por el monto total)")
    print("   2. Pagos parciales (anticipo + cuotas + saldo final)")
    
    while True:
        try:
            choice = input("\nElige una opción (1-2): ").strip()
            if choice in ["1", "2"]:
                return choice == "2"  # True si quiere cuotas
            else:
                print("⚠️ Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\n\n❌ Operación cancelada.")
            return False

def run_cxc(generar_cuotas=False):
    """Ejecuta la generación de CxC"""
    print("\n" + "=" * 70)
    print("📤 EJECUTANDO: Generación de Cuentas por Cobrar")
    print("=" * 70)
    
    # Importar y configurar el módulo
    import auto_generate_cxc_improved as cxc_module
    
    # Aplicar configuración
    cxc_module.CONFIG["generar_cuotas"] = generar_cuotas
    
    # Ejecutar
    cxc_module.main()

def run_cxp():
    """Ejecuta la generación de CxP"""
    print("\n" + "=" * 70)
    print("📥 EJECUTANDO: Generación de Cuentas por Pagar")
    print("=" * 70)
    
    # Importar y ejecutar
    import auto_generate_cxp as cxp_module
    cxp_module.main()

def main():
    print_header()
    
    choice = get_user_choice()
    
    if choice == "4":
        print("\n👋 Hasta luego!")
        return
    
    # Configurar según elección
    if choice in ["1", "3"]:
        generar_cuotas = configure_cxc()
    else:
        generar_cuotas = False
    
    # Ejecutar según elección
    if choice == "1":
        run_cxc(generar_cuotas)
    elif choice == "2":
        run_cxp()
    elif choice == "3":
        run_cxc(generar_cuotas)
        print("\n" + "⏸️ " * 35)
        input("Presiona ENTER para continuar con CxP...")
        run_cxp()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✨ PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    print("\n💡 Próximos pasos:")
    print("   • Revisa las cuentas creadas en Notion")
    print("   • Verifica las relaciones con proyectos y clientes/proveedores")
    print("   • Ajusta estados y fechas si es necesario")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Programa interrumpido por el usuario.")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
