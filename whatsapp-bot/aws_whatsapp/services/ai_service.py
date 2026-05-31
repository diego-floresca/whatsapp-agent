import os
import base64
from anthropic import Anthropic
from aws_whatsapp.config.business_info import BUSINESS_CONTEXT

# Inicializar cliente de Anthropic
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
except Exception as e:
    print(f"❌ Error inicializando cliente Anthropic: {e}")

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
    Genera respuesta usando Anthropic API, opcionalmente inyectando audio o imagen.
    """
    try:
        messages = []
        
        # 1. Reconstruir historial previo
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            
            # Evitamos procesar audios/imágenes del historial para ahorrar tokens/errores
            if "[AUDIO:" in content or "[IMAGEN:" in content: 
                continue 
                
            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "ai":
                messages.append({"role": "assistant", "content": content})
        
        # 2. Si es el primer mensaje, o todos fueron audios/imágenes filtrados
        if not messages:
            messages.append({"role": "user", "content": "Hola"})

        # 3. Preparar el contenido del último mensaje del usuario si hay adjuntos
        last_message_content = []
        
        if image_bytes:
            print("📸 Procesando imagen para Anthropic...")
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            media_type = image_type or 'image/jpeg'
            
            last_message_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_b64,
                    }
                }
            )
            last_message_content.append({"type": "text", "text": "El usuario envió esta imagen. Responde apropiadamente."})
            
        elif audio_bytes:
            print("🎙️ Procesando audio (no soportado nativamente como binario en Claude texto)...")
            last_message_content.append({"type": "text", "text": "[El usuario envió un audio pero este sistema no procesa audio directamente aún. Pídele amablemente que lo escriba.]"})
            
        # Si hay contenido multimedia nuevo, reemplazamos el último mensaje de usuario o agregamos uno nuevo
        if last_message_content:
            if messages and messages[-1]["role"] == "user":
                # Si el último mensaje es del usuario, convertimos su string a lista y le agregamos la imagen
                original_text = messages[-1]["content"]
                if isinstance(original_text, str):
                    messages[-1]["content"] = last_message_content + [{"type": "text", "text": original_text}]
            else:
                messages.append({"role": "user", "content": last_message_content})

        # 4. Invocar modelo de Anthropic
        print("🤖 Invocando Anthropic API...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"❌ Error IA (Anthropic): {e}")
        return "Tuve un problema técnico procesando tu mensaje. ¿Podrías escribirlo de nuevo?"