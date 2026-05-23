from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from gcp_whatsapp.config.business_info import BUSINESS_CONTEXT

# Configuración del modelo (Gemini Pro es rápido y económico para chat)
# Vertex AI tomará automáticamente las credenciales del entorno (gcloud auth...)
llm = ChatVertexAI(
    model_name="gemini-2.5-flash", # O "gemini-pro" (Flash es más rápido para chat)
    temperature=0.7,
    max_output_tokens=1024, # Respuestas concisas para WhatsApp
    location="us-central1" # aun no soporta northamerica-south1
)

SYSTEM_PROMPT = f"""
Eres un asistente virtual experto trabajando para la empresa descrita abajo.
Tu objetivo es atender a los clientes por WhatsApp, resolver dudas y concretar ventas/citas.

INFORMACIÓN DEL NEGOCIO:
{BUSINESS_CONTEXT}

REGLAS DE COMPORTAMIENTO:
1. RESPUESTAS CORTAS: WhatsApp es chat rápido. No escribas emails largos. Máximo 3 párrafos cortos.
2. PRECIOS: Solo da precios que estén explícitamente en la información. Si no sabes, di "déjame consultarlo con un humano".
3. FORMATO: Usa **negritas** para precios o datos clave. No uses Markdown complejo (tablas, headers #).
4. AUDIO: Si te mandan audio, resume lo que entendiste antes de responder.
5. IDIOMA: Español latino neutro.

Si el usuario pregunta algo fuera de este contexto, responde amablemente que solo puedes ayudar con temas de la empresa.
"""

def generate_ai_response(chat_history: list, audio_bytes=None, audio_type=None, image_bytes=None, image_type=None) -> str:
    """
    Genera respuesta, opcionalmente inyectando audio o imagen al prompt.
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # 1. Reconstruir historial de texto previo
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            # Ignoramos mensajes que sean solo marcadores de [AUDIO] o [IMAGEN] para no confundir al modelo
            if "[AUDIO:" in content or "[IMAGEN:" in content: 
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
        
        # 3. Si hay imagen nueva, la agregamos como mensaje multimodal
        if image_bytes:
            print("📸 Enviando imagen a Gemini...")
            message_content = [
                {"type": "text", "text": "El usuario envió esta imagen:"},
                {
                    "type": "media", 
                    "mime_type": image_type or "image/jpeg",
                    "data": image_bytes
                }
            ]
            messages.append(HumanMessage(content=message_content))
            
        # 4. Invocar modelo
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return "Tuve un problema técnico procesando tu mensaje. ¿Podrías escribirlo?"