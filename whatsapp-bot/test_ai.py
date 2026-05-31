import os
from dotenv import load_dotenv

# Cargamos el .env local para que agarre el ANTHROPIC_API_KEY
load_dotenv()

# Importamos la función que acabamos de reescribir
from aws_whatsapp.services.ai_service import generate_ai_response

def main():
    print("Iniciando prueba local de la API de Anthropic...")
    
    # Simulamos un historial de chat
    historial = [
        {"role": "user", "content": "Hola, ¿cómo estás?"},
        {"role": "ai", "content": "¡Hola! Muy bien, soy el asistente virtual. ¿En qué te puedo ayudar?"},
        {"role": "user", "content": "¿A qué se dedica tu empresa?"}
    ]
    
    try:
        # Llamamos a nuestra función
        respuesta = generate_ai_response(chat_history=historial)
        print("\n=== RESPUESTA DEL BOT ===")
        print(respuesta)
        print("=========================\n")
        print("✅ ¡El modelo y tu código están funcionando perfectamente!")
    except Exception as e:
        print(f"\n❌ Hubo un error durante la prueba: {e}")

if __name__ == "__main__":
    main()
