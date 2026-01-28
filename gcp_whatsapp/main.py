import os
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from typing import Dict, Any

# Importamos nuestros servicios de base de datos
# Asegúrate de que la ruta de importación coincida con tu estructura
from gcp_whatsapp.services.firestore_service import get_or_create_user, add_message, get_chat_history
from gcp_whatsapp.services.ai_service import generate_ai_response 
from gcp_whatsapp.services.messenger_service import send_whatsapp_message
# Configuración de Logs (Fundamental para GCP)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CONFIGURACIÓN ---
# En Cloud Run, estas variables vendrán del entorno (Environment Variables)
# Para local, puedes definirlas aquí o usar python-dotenv
WEBHOOK_VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "MI_TOKEN_SECRETO_TEMPORAL")

@app.get("/")
async def health_check():
    """Endpoint simple para saber si el servicio está vivo en Cloud Run."""
    return {"status": "alive", "service": "whatsapp-agent-core"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    VERIFICACIÓN DE META:
    Este endpoint es llamado por Meta cuando configuras la URL del webhook.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook verificado correctamente.")
            # Meta espera que devolvamos SOLO el challenge como entero/texto plano
            return int(challenge)
        else:
            logger.error("❌ Token de verificación incorrecto.")
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    
    raise HTTPException(status_code=400, detail="Missing parameters")

@app.post("/webhook")
async def receive_whatsapp_event(request: Request, background_tasks: BackgroundTasks):
    """
    RECEPCIÓN DE MENSAJES:
    Recibe el evento, devuelve 200 OK rápido y procesa en background.
    """
    try:
        payload = await request.json()
        
        # Procesamos en background para no bloquear la respuesta a Meta
        background_tasks.add_task(process_incoming_message, payload)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error recibiendo evento: {e}")
        # Aun si fallamos, es mejor devolver 200 para que Meta no siga reintentando infinitamente
        return {"status": "error", "message": str(e)}

async def process_incoming_message(payload: Dict[Any, Any]):
    """
    Lógica principal: Parsear JSON -> Guardar en DB -> (Futuro: Llamar IA)
    """
    try:
        # Exploramos el JSON de Meta (es anidado y complejo)
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        # Verificamos si es un mensaje (y no un cambio de estado como "leído")
        if "messages" in value:
            message_data = value["messages"][0]
            contact_data = value["contacts"][0]
            
            # 1. Extraer datos clave
            wa_id = contact_data.get("wa_id") # Número telefónico (ID usuario)
            name = contact_data.get("profile", {}).get("name", "Unknown")
            message_body = message_data.get("text", {}).get("body", "")
            msg_type = message_data.get("type")

            if msg_type != "text":
                logger.warning(f"Recibido mensaje tipo {msg_type}. Por ahora solo manejamos texto.")
                # TODO: Implementar manejo de imágenes/audio aquí
                return

            logger.info(f"📩 Mensaje recibido de {name} ({wa_id}): {message_body}")

            # 2. Interacción con Firestore (Tu capa de persistencia)
            # Paso A: Asegurar usuario
            get_or_create_user(phone_number=wa_id, name=name)
            
            # Paso B: Guardar mensaje del usuario
            add_message(phone_number=wa_id, role="user", content=message_body)
            logger.info("✅ Mensaje de usuario guardado.")

            # 3. AQUÍ VA EL CEREBRO DE LA IA (Próximos pasos)
            
            # A. Recuperar contexto (últimos 10 mensajes incluyendo el nuevo)
            history = get_chat_history(phone_number=wa_id, limit=10)
            
            # B. Generar respuesta con Gemini
            ai_reply = generate_ai_response(history)
            
            # C. Guardar la respuesta de la IA en Firestore
            add_message(phone_number=wa_id, role="ai", content=ai_reply)
            logger.info(f"🤖 Respuesta IA generada y guardada: {ai_reply}")

            # 4. ENVIAR A WHATSAPP 
            # IMPORTANTE: Meta cobra por conversación, no por mensaje (dentro de la ventana de 24h).
            send_whatsapp_message(to_number=wa_id, message_body=ai_reply)
         
            logger.info("✅ Ciclo completo: Recibido -> Guardado -> Pensado -> Enviado")            
    except IndexError:
        # A veces llegan eventos vacíos o de control, los ignoramos
        pass
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje en background: {e}")
