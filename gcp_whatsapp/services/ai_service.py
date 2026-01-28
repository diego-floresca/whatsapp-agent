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
Eres un asistente experto y amable para una empresa. 
Tu objetivo es ayudar a los clientes por WhatsApp de manera concisa y útil.
No uses markdown complejo (negritas ** son permitidas).
Responde siempre en español neutro.
"""

def generate_ai_response(chat_history: list) -> str:
    """
    Toma el historial de Firestore (lista de dicts), lo convierte 
    a formato LangChain e invoca a Gemini.
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Convertir historial de diccionarios a objetos Message de LangChain
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
        
        # Invocamos al modelo
        print("🤖 Consultando a Vertex AI (Gemini)...")
        response = llm.invoke(messages)
        
        return response.content
        
    except Exception as e:
        print(f"❌ Error generando respuesta de IA: {e}")
        return "Lo siento, estoy teniendo problemas técnicos momentáneos."