import sys
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Cargar variables de entorno MANUALMENTE para asegurar que lea el archivo correcto
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

from email_sender import enviar_email

def test_real_email():
    print("Iniciando prueba de envio de correo...")
    
    # Verificar que se hayan cargado las credenciales
    user = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    
    print(f"📧 Usuario leido desde .env: {user}")
    if not password:
        print("❌ ERROR: No se detectó EMAIL_PASSWORD en el .env")
        return
    else:
        print("🔑 Contraseña leída correctamente (oculta).")

    # Enviamos el correo de prueba a tu dirección directa
    destinatario = "gonzavolante@gmail.com" 

    print(f"📤 Enviando informe de prueba a: {destinatario}...")
    
    exito, mensaje = enviar_email(
        destinatario=destinatario,
        nombre_cliente="Robles (Cliente de Prueba)",
        link_informe="https://administracion-ne.github.io/informes-fv/Informes_01_2026/informe_3011513_Robles.html",
        periodo="Enero 2026",
        metricas={
            'consumo_total': 12500,
            'generacion': 4500,
            'ahorro_estimado': 120500
        },
        callback_log=print
    )
    
    if exito:
        print("\n✅ ¡El correo de prueba ha sido ENVIADO CON ÉXITO!")
        print("Por favor, revisa tu bandeja de entrada (y la de correo no deseado/spam por las dudas).")
    else:
        print(f"\n❌ Hubo un error al enviar el correo: {mensaje}")

if __name__ == "__main__":
    test_real_email()
