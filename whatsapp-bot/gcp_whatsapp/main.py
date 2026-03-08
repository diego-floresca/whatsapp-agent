import os
import logging
import uuid
import mimetypes
from fastapi import FastAPI, Request, BackgroundTasks

# Imports de servicios
from gcp_whatsapp.services.firestore_service import get_or_create_user, add_message, get_chat_history
from gcp_whatsapp.services.messenger_service import send_whatsapp_message,send_whatsapp_audio
from gcp_whatsapp.services.ai_service import generate_ai_response
from gcp_whatsapp.services.audio_service import get_audio_url, download_audio_bytes, upload_to_gcs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
WEBHOOK_VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN")

@app.get("/webhook")
async def verify_webhook(request: Request):
    # (Tu código de verificación GET sigue igual, no lo toques)
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == WEBHOOK_VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return {"status": "error"}

@app.post("/webhook")
async def receive_whatsapp_event(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        background_tasks.add_task(process_incoming_message, payload)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error"}

async def process_incoming_message(payload):
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        if "messages" in value:
            message_data = value["messages"][0]
            contact_data = value["contacts"][0]
            wa_id = contact_data.get("wa_id")
            name = contact_data.get("profile", {}).get("name", "Unknown")
            
            # Aseguramos usuario
            get_or_create_user(phone_number=wa_id, name=name)
            
            msg_type = message_data.get("type")
            
            # --- CASO 1: TEXTO ---
            if msg_type == "text":
                text_body = message_data.get("text", {}).get("body", "")
                logger.info(f"📩 Texto de {name}: {text_body}")
                
                add_message(wa_id, "user", text_body)
                
                # IA solo texto
                history = get_chat_history(wa_id)
                reply = generate_ai_response(history)
                
                add_message(wa_id, "ai", reply)
                send_whatsapp_message(wa_id, reply)

            # --- CASO 2: AUDIO ---
            elif msg_type == "audio":
                audio_id = message_data.get("audio", {}).get("id")
                mime_type = message_data.get("audio", {}).get("mime_type", "audio/ogg")
                logger.info(f"🎙️ Audio recibido ID: {audio_id}")
                
                # 1. Bajar
                url = get_audio_url(audio_id)
                if url:
                    audio_bytes, content_type = download_audio_bytes(url)
                    if audio_bytes:
                        # 2. Subir a GCS
                        ext = mimetypes.guess_extension(content_type) or ".ogg"
                        filename = f"{wa_id}_{uuid.uuid4()}{ext}"
                        gcs_uri = upload_to_gcs(audio_bytes, filename, content_type)
                        
                        # 3. Guardar referencia (no el audio) en Firestore
                        add_message(wa_id, "user", f"[AUDIO ENVIADO: {gcs_uri}]", msg_type="audio")
                        
                        # 4. IA Multimodal (pasamos bytes directos para velocidad)
                        # Recuperamos contexto previo de texto
                        history = get_chat_history(wa_id, limit=5)
                        reply = generate_ai_response(history, audio_bytes=audio_bytes, audio_type=content_type)
                        
                        # 5. Responder
                        add_message(wa_id, "ai", reply)
                        send_whatsapp_message(wa_id, reply)
    except Exception as e:
        logger.error(f"❌ Error procesando: {e}")