import os
from dotenv import load_dotenv

load_dotenv()

from aws_whatsapp.services.ai_service import generate_ai_response

SEPARADOR = "\n" + "=" * 60 + "\n"


def run_test(nombre: str, historial: list, phone_number: str = "5219991234567"):
    print(f"{SEPARADOR}🧪 TEST: {nombre}{SEPARADOR}")
    for msg in historial:
        rol = "Usuario" if msg["role"] == "user" else "Bot"
        print(f"  [{rol}]: {msg['content']}")
    print("\n  [Bot procesando...]\n")

    respuesta = generate_ai_response(
        chat_history=historial,
        phone_number=phone_number,
    )
    print(f"  [Bot]: {respuesta}")
    print(SEPARADOR)
    return respuesta


def main():
    print("🚀 Iniciando pruebas locales del bot de soporte Rappi\n")

    # --- TEST 1: Reembolso aprobado automáticamente (RPP-001: no entregada, GPS sin confirmación, monto bajo) ---
    run_test(
        nombre="Reembolso APROBADO — orden no entregada (RPP-001)",
        historial=[
            {"role": "user", "content": "Hola, mi pedido no llegó"},
            {"role": "ai", "content": "Hola, lamento escuchar eso. ¿Me puedes dar el número de tu orden para revisarlo?"},
            {"role": "user", "content": "Sí, es el RPP-001"},
        ],
    )

    # --- TEST 2: Caso que escala — GPS confirma entrega pero usuario dice que no llegó (RPP-003) ---
    run_test(
        nombre="Escalamiento — inconsistencia GPS (RPP-003)",
        historial=[
            {"role": "user", "content": "Mi orden RPP-003 no llegó, quiero mi dinero de vuelta"},
        ],
    )

    # --- TEST 3: Mensaje ambiguo / fuera de contexto ---
    run_test(
        nombre="Fuera de contexto — pregunta no relacionada",
        historial=[
            {"role": "user", "content": "¿Cuánto cuesta suscribirme a Rappi Prime?"},
        ],
    )


if __name__ == "__main__":
    main()
