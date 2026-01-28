import functions_framework
import vertexai
from vertexai.generative_models import GenerativeModel
from twilio.rest import Client  # <--- Importamos el cliente para enviar mensajes proactivamente

# --- CONFIGURACIÓN ---
PROJECT_ID = "agente-whatsapp-gemini"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.5-flash"

# CREDENCIALES DE TWILIO (Idealmente usar variables de entorno, por ahora ponlas aquí)
TWILIO_ACCOUNT_SID = "AC7ce15c01bbb7f47e78acdd8b6f72f202" 
TWILIO_AUTH_TOKEN = "8292cdf35795834e380814e6f604005e"

# Inicialización
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_ID)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@functions_framework.http
def whatsapp_webhook(request):
    """
    1. Recibe el mensaje.
    2. Procesa con Gemini (Sin memoria).
    3. Envía la respuesta vía API de Twilio.
    4. Retorna 'OK' para cerrar la conexión.
    """
    
    # 1. Obtener datos
    form_data = request.form
    incoming_msg = form_data.get('Body', '').strip()
    sender = form_data.get('From', '') # El número del usuario
    to_number = form_data.get('To', '') # El número del Sandbox (whatsapp:...)

    print(f"Mensaje recibido de {sender}: {incoming_msg}")

    if not incoming_msg:
        return "No text", 200

    try:
        # 2. Consultar a Gemini (Directo, sin historial)
        # Usamos generate_content en lugar de start_chat porque no hay memoria
        response = model.generate_content(incoming_msg)
        response_text = response.text

        print(f"Respuesta generada ({len(response_text)} chars). Enviando...")

        # 3. Enviar respuesta proactiva con Cliente Twilio
        # Esto permite enviar mensajes largos o tardar un poco más
        message = twilio_client.messages.create(
            from_=to_number,
            body=response_text,
            to=sender
        )
        print(f"Mensaje enviado con éxito. SID: {message.sid}")

    except Exception as e:
        print(f"Error procesando/enviando: {e}")
        # Opcional: Avisar al usuario del error
        # twilio_client.messages.create(from_=to_number, body="Error en el sistema", to=sender)

    # 4. Responder al Webhook de Twilio para que sepa que todo salió bien
    return "OK", 200

