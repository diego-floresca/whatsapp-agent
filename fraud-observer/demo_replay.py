"""
demo_replay.py — Inserta en Firestore el caso viral de estafa (falso soporte)
mensaje por mensaje con pausas de 2-3 segundos, para verlo en vivo en el dashboard
con el score de riesgo subiendo en tiempo real.

Uso:
    cd fraud-observer
    python demo_replay.py [--wa-id +521234567890]
"""

import argparse
import os
import time
from dotenv import load_dotenv

load_dotenv()

from google.cloud import firestore


DEMO_CONVERSATION = [
    {
        "sender": "usuario",
        "role": "user",
        "text": "Hola, ¿ya viene mi pedido? Llevo media hora esperando.",
        "delay": 0,
    },
    {
        "sender": "repartidor",
        "role": "human",
        "text": "Hola, sí ya lo tengo. Voy en camino, como 5 minutos.",
        "delay": 2,
    },
    {
        "sender": "usuario",
        "role": "user",
        "text": "Ok gracias.",
        "delay": 2,
    },
    {
        "sender": "repartidor",
        "role": "human",
        "text": "Disculpa, la plataforma de Rappi está caída en este momento y no me deja marcar el pedido como en camino.",
        "delay": 3,
    },
    {
        "sender": "usuario",
        "role": "user",
        "text": "¿En serio? Raro, a mí sí me llegó la notificación.",
        "delay": 2,
    },
    {
        "sender": "repartidor",
        "role": "human",
        "text": "Sí, es del lado del repartidor. Para poder continuar el sistema requiere que confirmes tu identidad con el código de verificación que te acaba de llegar al correo o SMS.",
        "delay": 3,
    },
    {
        "sender": "usuario",
        "role": "user",
        "text": "Me llegó un mensaje con un número de 6 dígitos...",
        "delay": 2,
    },
    {
        "sender": "repartidor",
        "role": "human",
        "text": "Sí ese, dímelo rápido por favor que el sistema tiene un tiempo límite y si no lo confirmas se cancela el pedido automáticamente.",
        "delay": 2,
    },
    {
        "sender": "usuario",
        "role": "user",
        "text": "Espera, eso no me suena bien. El código que me llegó dice 'No compartas este código con nadie'.",
        "delay": 3,
    },
    {
        "sender": "repartidor",
        "role": "human",
        "text": "Sí eso lo ponen siempre pero para casos de soporte es diferente. Confía en mí, soy de Rappi.",
        "delay": 2,
    },
    {
        "sender": "usuario",
        "role": "user",
        "text": "No, esto es una estafa. No voy a dar el código.",
        "delay": 2,
    },
]


def main():
    parser = argparse.ArgumentParser(description='Demo replay de conversación de estafa')
    parser.add_argument(
        '--wa-id',
        default='+521234567890',
        help='Número de teléfono destino en formato E.164 (default: +521234567890)',
    )
    args = parser.parse_args()

    wa_id = args.wa_id
    project = os.environ.get('PROJECT_ID')
    database = os.environ.get('DATABASE_NAME', '(default)')

    print(f'🎬 Demo replay iniciando...')
    print(f'   WA ID: {wa_id}')
    print(f'   Firestore: {project}/{database}')
    print()

    db = firestore.Client(project=project, database=database)
    user_ref = db.collection('users').document(wa_id)

    # Crear/resetear el usuario de demo
    user_ref.set({
        'name': 'Demo Usuario (Rappi)',
        'phone_number': wa_id,
        'ai_enabled': False,
        'status': 'en_curso',
        'last_interaction': firestore.SERVER_TIMESTAMP,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    # Limpiar mensajes anteriores de este demo
    existing = user_ref.collection('messages').stream()
    for doc in existing:
        doc.reference.delete()

    # Limpiar fraud score anterior
    fraud_ref = db.collection('fraud_scores').document(wa_id)
    fraud_ref.delete()

    print(f'✅ Usuario de demo inicializado. Insertando mensajes...\n')

    for i, msg in enumerate(DEMO_CONVERSATION, 1):
        if msg['delay'] > 0:
            print(f'   ⏳ Esperando {msg["delay"]}s...')
            time.sleep(msg['delay'])

        sender_label = '👤 Usuario' if msg['sender'] == 'usuario' else '🛵 Repartidor'
        print(f'   {sender_label}: {msg["text"][:80]}...' if len(msg['text']) > 80 else f'   {sender_label}: {msg["text"]}')

        # Insertar mensaje en Firestore
        user_ref.collection('messages').add({
            'role': msg['role'],
            'content': msg['text'],
            'type': 'text',
            'timestamp': firestore.SERVER_TIMESTAMP,
        })

        # Actualizar last_interaction del usuario para disparar el listener
        user_ref.update({'last_interaction': firestore.SERVER_TIMESTAMP})

        print(f'   [Mensaje {i}/{len(DEMO_CONVERSATION)} insertado en Firestore]')

    print()
    print('🎬 Demo completado. Revisa el dashboard para ver el score de riesgo.')
    print('   Si el fraud-observer está corriendo, debió detectar la estafa y enviar SMS.')


if __name__ == '__main__':
    main()
