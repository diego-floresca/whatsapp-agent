"""
Envía SMS de alerta al usuario vía Twilio.
El número destino es el mismo waId (número E.164) de la conversación de WhatsApp.
"""

import os
from twilio.rest import Client


_ALERT_TEMPLATE = (
    "Rappi Seguridad: nunca compartas tu código de verificación ni hagas depósitos "
    "fuera de la app, aunque digan que es soporte o que hay un problema con tu pedido. "
    "Si esto te pidieron en tu chat, repórtalo en la app."
)


def send_alert(wa_id: str, scam_type: str | None = None) -> bool:
    """
    Envía SMS al número wa_id.

    Args:
        wa_id: número en formato E.164 (ej. +521234567890)
        scam_type: tipo de estafa detectado (solo para logging)

    Returns:
        True si el SMS fue aceptado por Twilio, False si falló.
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_FROM_NUMBER')

    if not all([account_sid, auth_token, from_number]):
        print('[twilio_alert] Credenciales de Twilio incompletas — SMS no enviado')
        return False

    # Asegurar que el número tenga prefijo +
    to_number = wa_id if wa_id.startswith('+') else f'+{wa_id}'

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=_ALERT_TEMPLATE,
            from_=from_number,
            to=to_number,
        )
        print(f'[twilio_alert] SMS enviado a {to_number} — SID: {message.sid} — scam_type: {scam_type}')
        return True
    except Exception as e:
        print(f'[twilio_alert] Error enviando SMS a {to_number}: {e}')
        return False
