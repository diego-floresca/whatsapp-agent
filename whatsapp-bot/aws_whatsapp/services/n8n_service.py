import os
import requests
import logging

logger = logging.getLogger(__name__)

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")

def forward_payload_to_n8n(payload: dict):
    """
    Envía el payload completo del webhook de WhatsApp hacia n8n.
    """
    if not N8N_WEBHOOK_URL:
        # Si no hay URL configurada, simplemente no hacemos nada
        return
        
    try:
        # Timeout de 3 segundos para no bloquear demasiado el hilo
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=3)
        response.raise_for_status()
        logger.info(f"✅ Payload enviado a n8n: {response.status_code}")
    except requests.exceptions.Timeout:
        logger.warning("⏱️ Timeout al intentar enviar webhook a n8n")
    except Exception as e:
        logger.error(f"❌ Error reenviando a n8n: {e}")
