import re
import json
import logging
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from gcp_whatsapp.config.business_info import BUSINESS_CONTEXT

logger = logging.getLogger(__name__)

llm = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.7,
    max_output_tokens=1024,
    location="us-central1",
    generation_config={
        "response_mime_type": "application/json"  # Fuerza a Gemini a responder SIEMPRE con JSON válido
    }
)

SYSTEM_PROMPT = f"""
Eres un asistente virtual experto trabajando para la empresa descrita abajo.
Tu objetivo es atender a los clientes por WhatsApp, resolver dudas y concretar ventas/citas.

INFORMACIÓN DEL NEGOCIO:
{BUSINESS_CONTEXT}

REGLAS DE COMPORTAMIENTO:
1. RESPUESTAS CORTAS: WhatsApp es chat rápido. No escribas emails largos. Máximo 3 párrafos cortos.
2. PRECIOS: Solo da precios que estén explícitamente en la información. Si no sabes, di "déjame consultarlo con un humano".
3. FORMATO: Usa *negritas* para precios o datos clave. No uses Markdown complejo (tablas, headers #).
4. AUDIO: Si te mandan audio, resume lo que entendiste antes de responder.
5. IDIOMA: Español latino neutro.

Si el usuario pregunta algo fuera de este contexto, responde amablemente que solo puedes ayudar con temas de la empresa.

---

FORMATO DE RESPUESTA OBLIGATORIO — responde ÚNICAMENTE con este JSON, sin texto antes ni después, sin bloques de código:

{{
  "mensaje": "Tu respuesta conversacional aquí, la que el usuario verá en WhatsApp",
  "estado": "en_curso",
  "tipo_problema": "pago"
}}

VALORES VÁLIDOS:
- "estado": "en_curso" | "resuelto" | "sin_resolver"
- "tipo_problema": "pago" | "estacionamiento" | "facturacion" | "tag" | "app" | "multa" | "ventas" | "otro"

REGLAS DE ESTADO:
- "en_curso": conversación activa, el usuario no se ha despedido.
- "resuelto": SOLO cuando uses la frase exacta "¡Fue un placer atenderte! ¿Puedo ayudarte en algo más? 😊"
- "sin_resolver": SOLO cuando uses la frase exacta "Disculpa, te transferiré con un agente humano para darte mejor ayuda 🙏"

CRÍTICO: El campo "mensaje" es lo único que el usuario verá. "estado" y "tipo_problema" son internos.
"""

def _parse_response(raw: str) -> dict:
    """
    Extrae JSON del response de Gemini aunque venga con texto antes o después,
    o dentro de bloques de código.
    """
    # Limpiar bloques de código ```json ... ```
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    raw = raw.strip()

    # Intentar parsear directo
    try:
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError:
        pass

    # Buscar el primer objeto JSON válido en el string
    json_match = re.search(r'\{[\s\S]*?\}(?=\s*$|\s*\n)', raw)
    if not json_match:
        # Intento más agresivo — tomar todo entre primer { y último }
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(raw[start:end+1])
                return parsed
            except json.JSONDecodeError:
                pass

    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            return parsed
        except json.JSONDecodeError:
            pass

    return None


def generate_ai_response(chat_history: list, audio_bytes=None, audio_type=None, image_bytes=None, image_type=None) -> dict:
    """
    Genera respuesta estructurada {mensaje, estado, tipo_problema}.
    """
    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        # 1. Reconstruir historial de texto previo
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if "[AUDIO:" in content or "[IMAGEN:" in content:
                continue
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))

        # 2. Audio multimodal
        if audio_bytes:
            logger.info("🎙️ Enviando audio a Gemini...")
            messages.append(HumanMessage(content=[
                {"type": "text", "text": "El usuario envió este audio:"},
                {"type": "media", "mime_type": audio_type or "audio/ogg", "data": audio_bytes}
            ]))

        # 3. Imagen multimodal
        if image_bytes:
            logger.info("📸 Enviando imagen a Gemini...")
            messages.append(HumanMessage(content=[
                {"type": "text", "text": "El usuario envió esta imagen:"},
                {"type": "media", "mime_type": image_type or "image/jpeg", "data": image_bytes}
            ]))

        # 4. Invocar modelo
        response = llm.invoke(messages)
        raw = response.content.strip()
        logger.info(f"🔍 RAW GEMINI: {raw[:200]}")

        # 5. Parsear respuesta
        parsed = _parse_response(raw)

        if parsed and "mensaje" in parsed:
            estado = parsed.get("estado", "en_curso")
            tipo = parsed.get("tipo_problema", "otro")

            # Validar valores permitidos
            if estado not in ("en_curso", "resuelto", "sin_resolver"):
                estado = "en_curso"
            if tipo not in ("pago", "estacionamiento", "facturacion", "tag", "app", "multa", "ventas", "otro"):
                tipo = "otro"

            logger.info(f"✅ Parsed OK — estado: {estado} | tipo: {tipo}")
            return {
                "mensaje": parsed["mensaje"],
                "estado": estado,
                "tipo_problema": tipo
            }

        # Fallback — Gemini no respetó el formato
        logger.warning(f"⚠️ No se pudo parsear JSON. Raw: {raw[:150]}")
        return {
            "mensaje": raw,
            "estado": "en_curso",
            "tipo_problema": "otro"
        }

    except Exception as e:
        logger.error(f"❌ Error IA: {e}")
        return {
            "mensaje": "Tuve un problema técnico. ¿Podrías repetir tu mensaje?",
            "estado": "en_curso",
            "tipo_problema": "otro"
        }
