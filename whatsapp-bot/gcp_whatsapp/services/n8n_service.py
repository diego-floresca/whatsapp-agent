import os
import httpx
import logging

logger = logging.getLogger(__name__)

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")  # Agregar al .env

def notify_conversation_closed(
    wa_id: str,
    name: str,
    estado: str,
    tipo_problema: str,
    chat_history: list
) -> None:
    """
    Dispara el webhook a n8n cuando una conversación se cierra
    (estado = "resuelto" o "sin_resolver").
    
    n8n se encarga de:
    - Clasificar y enriquecer con LLM
    - Notificar a Slack
    - Crear ticket en Monday si es sin_resolver
    - Registrar en Airtable
    """
    if not N8N_WEBHOOK_URL:
        logger.warning("⚠️ N8N_WEBHOOK_URL no configurada. Skipping notificación.")
        return

    # Construir resumen de la conversación (últimos 10 mensajes)
    resumen_mensajes = [
        {"role": msg.get("role"), "content": msg.get("content")}
        for msg in chat_history[-10:]
        if not any(marker in msg.get("content", "") for marker in ["[AUDIO", "[IMAGEN"])
    ]

    payload = {
        "wa_id": wa_id,
        "nombre": name,
        "estado": estado,           # "resuelto" | "sin_resolver"
        "tipo_problema": tipo_problema,
        "historial": resumen_mensajes,
        "total_mensajes": len(chat_history)
    }

    try:
        # httpx sincrónico — fire and forget, no bloqueamos el flujo principal
        with httpx.Client(timeout=5.0) as client:
            response = client.post(N8N_WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                logger.info(f"✅ n8n notificado — {wa_id} | {estado} | {tipo_problema}")
            else:
                logger.warning(f"⚠️ n8n respondió {response.status_code}: {response.text[:100]}")
    except httpx.TimeoutException:
        logger.warning(f"⚠️ Timeout al notificar a n8n para {wa_id} — se ignora y sigue.")
    except Exception as e:
        logger.error(f"❌ Error al notificar a n8n: {e}")
