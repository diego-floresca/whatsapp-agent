from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Configuración del modelo (Gemini Pro es rápido y económico para chat)
# Vertex AI tomará automáticamente las credenciales de tu entorno (gcloud auth...)
llm = ChatVertexAI(
    model_name="gemini-2.5-flash", # O "gemini-pro" (Flash es más rápido para chat)
    temperature=0.7,
    max_output_tokens=256, # Respuestas concisas para WhatsApp
    location="us-central1" # Ajusta a tu región si es necesario
)

SYSTEM_PROMPT = """
Eres un asistente experto y amable de una empresa mexicana.
Puedes escuchar audios y leer texto.
Si recibes un audio, escucha atentamente y responde a la duda del usuario.
Responde siempre en texto en español conciso para WhatsApp.
"""

def generate_ai_response(chat_history: list, audio_bytes=None, audio_type=None) -> str:
    """
    Genera respuesta, opcionalmente inyectando audio al prompt.
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # 1. Reconstruir historial de texto previo
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            # Ignoramos mensajes que sean solo marcadores de [AUDIO] para no confundir al modelo
            if "[AUDIO:" in content: 
                continue 
                
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
        
        # 2. Si hay audio nuevo, lo agregamos al final como mensaje multimodal
        if audio_bytes:
            print("🎙️ Enviando audio a Gemini...")
            message_content = [
                {"type": "text", "text": "El usuario envió este audio:"},
                {
                    "type": "media",
                    "mime_type": audio_type or "audio/ogg",
                    "data": audio_bytes
                }
            ]
            messages.append(HumanMessage(content=message_content))
            
        # 3. Invocar modelo
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return "Tuve un problema técnico procesando tu mensaje. ¿Podrías escribirlo?"