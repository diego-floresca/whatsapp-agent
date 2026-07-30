"""
Desactiva (o reactiva) la IA para uno o todos los usuarios en Firestore.

Uso:
    # Desactivar para un número específico
    python disable_ai.py --wa-id +521234567890

    # Desactivar para TODOS los usuarios (modo demo)
    python disable_ai.py --all

    # Reactivar para todos
    python disable_ai.py --all --enable
"""

import argparse
from dotenv import load_dotenv
load_dotenv()

from services.firestore_listener import init_db

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wa-id', help='Número E.164 específico')
    parser.add_argument('--all', action='store_true', help='Aplica a todos los usuarios')
    parser.add_argument('--enable', action='store_true', help='Reactiva la IA (default: desactiva)')
    args = parser.parse_args()

    db = init_db()
    value = args.enable
    action = 'REACTIVANDO' if value else 'DESACTIVANDO'

    if args.all:
        docs = db.collection('users').stream()
        count = 0
        for doc in docs:
            doc.reference.update({'ai_enabled': value})
            print(f'  {action} IA para {doc.id}')
            count += 1
        print(f'\n✅ {action} IA para {count} usuario(s).')

    elif args.wa_id:
        db.collection('users').document(args.wa_id).update({'ai_enabled': value})
        print(f'✅ {action} IA para {args.wa_id}')

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
