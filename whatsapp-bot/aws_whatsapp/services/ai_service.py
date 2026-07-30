import os
import json
import base64
from anthropic import Anthropic
from aws_whatsapp.config.business_info import BUSINESS_CONTEXT
from aws_whatsapp.services.order_service import consultar_orden, evaluar_reembolso
from aws_whatsapp.services.ticket_service import crear_ticket

try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
except Exception as e:
    print(f"❌ Error inicializando cliente Anthropic: {e}")

SYSTEM_PROMPT = f"""
Eres el agente de primer contacto de soporte de Rappi por WhatsApp.
Tu objetivo NO es vender ni cerrar citas — es identificar el problema del usuario rápido, resolverlo si puedes, y si no, escalarlo a un humano con toda la información ya lista para actuar.

INFORMACIÓN DEL NEGOCIO Y POLÍTICAS:
{BUSINESS_CONTEXT}

REGLAS DE COMPORTAMIENTO:

1. TRIAGE PRIMERO: en tu primer o segundo mensaje, identifica a cuál de los motivos de contacto listados arriba corresponde el caso. Si el usuario no dio el número de orden, pídelo de inmediato — sin él no puedes avanzar.

2. NUNCA INVENTES DATOS DE LA ORDEN: no asumas montos, fechas, ni estados de entrega. Siempre usa la herramienta consultar_orden antes de decir cualquier cosa sobre el estado de un pedido.

3. NO PROMETAS UN REEMBOLSO SIN VERIFICAR: para reembolso, orden no entregada, o producto equivocado, usa evaluar_reembolso antes de confirmar cualquier compensación al usuario. Solo confirma un reembolso si la herramienta responde "aprobado".

4. ESCALA CUANDO CORRESPONDA, NO CUANDO TE RINDAS: si evaluar_reembolso responde "rechazado" o "ambiguo", o el motivo es cancelación/pago (siempre escala), usa crear_ticket_escalamiento con un resumen claro y específico y avísale al usuario que un agente humano seguirá su caso, sin prometer tiempos que no conoces.

5. RESPUESTAS CORTAS: WhatsApp es chat rápido. Máximo 3 párrafos cortos por mensaje.

6. FORMATO: Usa **negritas** para montos, estados o datos clave. Nada de Markdown complejo (tablas, headers #).

7. IMÁGENES: Si el usuario manda foto de un producto dañado, boleto o evidencia, analízala y resume lo que ves antes de continuar el flujo de resolución/escalamiento — la imagen es evidencia, inclúyela en el resumen si escalas.

8. AUDIO: Si te mandan audio, resume lo que entendiste antes de responder y continúa el flujo normal de triage.

9. TONO: Empático primero, resolutivo después — el usuario ya tiene un problema, no lo hagas sentir interrogado. Español latino neutro. Cero emojis de fiesta; máximo uno neutro si aplica (✅, 📦).

10. FUERA DE CONTEXTO: si la pregunta no tiene que ver con un problema de orden, responde amablemente que solo puedes ayudar con temas de soporte de pedidos.
"""

TOOLS = [
    {
        "name": "consultar_orden",
        "description": "Consulta los datos reales de una orden por su ID. Úsala antes de hacer cualquier afirmación sobre el estado de un pedido. Devuelve monto, estado de entrega, confirmación GPS, productos, y reembolsos previos del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "ID de la orden del usuario, por ejemplo RPP-001",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "evaluar_reembolso",
        "description": "Evalúa si una orden califica para reembolso automático según la política. Devuelve decision (aprobado, rechazado, o ambiguo) y la razón específica. Solo usar para motivos: orden_no_entregada, producto_equivocado, reembolso_solicitado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "ID de la orden a evaluar",
                },
                "motivo": {
                    "type": "string",
                    "description": "Motivo del contacto: orden_no_entregada, producto_equivocado, o reembolso_solicitado",
                },
            },
            "required": ["order_id", "motivo"],
        },
    },
    {
        "name": "crear_ticket_escalamiento",
        "description": "Crea un ticket de escalamiento para que un agente humano atienda el caso. Usar cuando el reembolso fue rechazado/ambiguo, o el motivo no es de resolución autónoma. El resumen debe ser específico y accionable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "ID de la orden relacionada al ticket",
                },
                "motivo": {
                    "type": "string",
                    "description": "Motivo del contacto identificado durante el triage",
                },
                "resumen": {
                    "type": "string",
                    "description": "Resumen estructurado y específico del caso para el agente humano. Incluye: qué reportó el usuario, datos relevantes de la orden, y por qué no se resolvió automáticamente.",
                },
                "prioridad": {
                    "type": "string",
                    "enum": ["alta", "media", "baja"],
                    "description": "Prioridad del ticket: alta (monto >$500 o cargo duplicado), media (producto equivocado o no entregado), baja (demora o consulta general)",
                },
                "phone_number": {
                    "type": "string",
                    "description": "Número de teléfono del usuario para que el agente pueda contactarlo",
                },
            },
            "required": ["order_id", "motivo", "resumen", "prioridad", "phone_number"],
        },
    },
]

MAX_TOOL_ITERATIONS = 5


def _execute_tool(tool_name: str, tool_input: dict, phone_number: str = "") -> dict:
    """Ejecuta la función Python correspondiente a un tool call de Claude."""
    print(f"🔧 Tool call: {tool_name} | args: {json.dumps(tool_input)}")

    if tool_name == "consultar_orden":
        result = consultar_orden(tool_input["order_id"])
    elif tool_name == "evaluar_reembolso":
        result = evaluar_reembolso(tool_input["order_id"], tool_input["motivo"])
    elif tool_name == "crear_ticket_escalamiento":
        result = crear_ticket(
            order_id=tool_input["order_id"],
            motivo=tool_input["motivo"],
            resumen=tool_input["resumen"],
            prioridad=tool_input["prioridad"],
            phone_number=tool_input.get("phone_number", phone_number),
        )
    else:
        result = {"error": True, "mensaje": f"Herramienta desconocida: {tool_name}"}

    print(f"✅ Tool result: {json.dumps(result, ensure_ascii=False)}")
    return result


def generate_ai_response(
    chat_history: list,
    audio_bytes=None,
    audio_type=None,
    image_bytes=None,
    image_type=None,
    phone_number: str = "",
) -> str:
    """
    Genera respuesta usando Anthropic API con tool use loop.
    Soporta hasta MAX_TOOL_ITERATIONS ciclos de function calling.
    """
    try:
        messages = []

        # 1. Reconstruir historial previo
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content", "")

            if "[AUDIO:" in content or "[IMAGEN:" in content:
                continue

            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "ai":
                messages.append({"role": "assistant", "content": content})

        if not messages:
            messages.append({"role": "user", "content": "Hola"})

        # 2. Inyectar media en el último mensaje si aplica
        last_message_content = []

        if image_bytes:
            print("📸 Procesando imagen para Anthropic...")
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            media_type = image_type or "image/jpeg"
            last_message_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_b64,
                    },
                }
            )
            last_message_content.append(
                {"type": "text", "text": "El usuario envió esta imagen como evidencia. Analízala y continúa el flujo de soporte."}
            )
        elif audio_bytes:
            print("🎙️ Audio recibido...")
            last_message_content.append(
                {
                    "type": "text",
                    "text": "[El usuario envió un audio. Resume brevemente que lo recibiste y pídele que escriba su problema para poder ayudarlo mejor.]",
                }
            )

        if last_message_content:
            if messages and messages[-1]["role"] == "user":
                original_text = messages[-1]["content"]
                if isinstance(original_text, str):
                    messages[-1]["content"] = last_message_content + [
                        {"type": "text", "text": original_text}
                    ]
            else:
                messages.append({"role": "user", "content": last_message_content})

        # 3. Tool use loop — máximo MAX_TOOL_ITERATIONS ciclos
        print("🤖 Invocando Anthropic API con tool use...")

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=TOOLS,
            )

            print(f"🔄 Iteración {iteration + 1} | stop_reason: {response.stop_reason}")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return "No pude generar una respuesta. Por favor intenta de nuevo."

            elif response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = _execute_tool(block.name, block.input, phone_number)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )

                messages.append({"role": "user", "content": tool_results})

            else:
                print(f"⚠️ stop_reason inesperado: {response.stop_reason}")
                break

        return "Tuve un problema procesando tu caso. Un agente humano te contactará pronto."

    except Exception as e:
        print(f"❌ Error IA (Anthropic): {e}")
        return "Tuve un problema técnico procesando tu mensaje. ¿Podrías escribirlo de nuevo?"
