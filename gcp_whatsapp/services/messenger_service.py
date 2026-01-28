import requests
import logging
import os

logger = logging.getLogger(__name__)

# CONFIGURACIÓN
# Cuando tengas la App aprobada, Meta te dará un token permanente (System User)
# Por ahora, usaremos una variable de entorno.
 
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID") 

def send_whatsapp_message(to_number: str, message_body: str):
    """
    Envía un mensaje de texto plano a WhatsApp usando la Graph API de Meta.
    """
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_body
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() # Lanza error si no es 200 OK
        logger.info(f"📤 Mensaje enviado a {to_number}: {response.json()}")
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        logger.error(f"❌ Error HTTP enviando a Meta: {err.response.text}")
    except Exception as e:
        logger.error(f"❌ Error general enviando mensaje: {e}")