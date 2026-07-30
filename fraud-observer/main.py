"""
fraud-observer — punto de entrada.

Carga variables de entorno, inicializa Firestore y arranca el listener.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from services.firestore_listener import init_db, start_listener


def main():
    print('🔍 fraud-observer arrancando...')
    init_db()
    start_listener()


if __name__ == '__main__':
    main()
