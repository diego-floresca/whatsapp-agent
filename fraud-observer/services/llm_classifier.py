"""
Capa 2: Clasificador LLM (Gemini via Vertex AI — mismo patrón que ai_service.py del bot).
Solo se invoca cuando la capa de reglas ya disparó — control de costo.

Usa ADC (gcloud auth application-default login), igual que Firestore. Sin API key extra.

Retorna: dict con keys risk_level, scam_type, evidence, reasoning
"""

import os
import re
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        # Import diferido: evita cargar el SDK de aiplatform al arrancar el observer
        from langchain_google_vertexai import ChatVertexAI  # noqa: PLC0415
        project = os.environ.get('PROJECT_ID', 'lunatic-analytics')
        _llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            temperature=0.1,
            max_output_tokens=8192,   # Gemini 2.5 Flash usa thinking tokens internos
            project=project,
            location="us-central1",
        )
    return _llm

_SYSTEM_PROMPT = """Eres un sistema experto en detección de fraude en conversaciones de entrega de Rappi (Colombia, México, Brasil).
Tu tarea: analizar la conversación y determinar si hay intento de estafa, identificando QUIÉN es el perpetrador y QUIÉN es la víctima.

IMPORTANTE: El fraude puede venir de CUALQUIER participante:
- REPARTIDOR/AGENTE → estafa al cliente (robo de OTP, falso soporte, redirección)
- CLIENTE/USUARIO → estafa al repartidor (propina falsa, pedir depósitos a terceros)
- TENDERO → estafa al cliente o repartidor (cobro fuera de la app, precios alterados)

TIPOS DE ESTAFA que debes detectar:
- robo_otp: pedir el código OTP/SMS/verificación con cualquier pretexto (perpetrador: agente/repartidor)
- robo_codigo_entrega: pedir el código de entrega ANTES de llegar para marcar como entregado sin entregar
- propina_falsa: cliente dice "te dejé propina" y luego pide al repartidor que deposite dinero a una cuenta externa (perpetrador: cliente)
- deposito_falso: cualquier solicitud de depósito, transferencia o pago fuera de la app, independientemente de quién lo pide
- redireccion_externa: dar otro número de WhatsApp/teléfono como "el oficial"
- cobro_externo: tendero o repartidor cobra aparte del precio mostrado en la app
- ninguno: la conversación es legítima

REGLA CRÍTICA — NO CONFUNDIR CON ESTAFA:
✅ LEGÍTIMOS:
  - "El código del portón es 1234" / "código postal" → NO es robo de OTP
  - "¿Me das el código de entrega cuando llegues?" → proceso normal si es al momento de entregar
  - "El pedido llegó frío / faltó algo" → reclamo legítimo
  - Mencionar "código" en contexto de portón/edificio/ubicación → NO es estafa

✅ FEW-SHOT LEGÍTIMOS:
Ejemplo 1 — Repartidor: "¿Cuál es el código del intercomunicador?"
→ LEGÍTIMO. Código de acceso al edificio. risk_level: bajo.

Ejemplo 2 — Usuario: "Mejor escríbeme por WhatsApp, aquí no me llegan."
→ LEGÍTIMO. Sin pedir datos sensibles. risk_level: bajo.

🚨 FEW-SHOT ESTAFAS:
Ejemplo 3 — Repartidor: "La plataforma está caída, comparte el código que te llegó al SMS."
→ ESTAFA. robo_otp. Perpetrador: repartidor. risk_level: alto.

Ejemplo 4 — Repartidor: "La propina no se procesó, deposita $200 a este Nequi: 3001234567."
→ ESTAFA. deposito_falso. Perpetrador: repartidor. risk_level: alto.

Ejemplo 5 — Cliente: "Oye te dejé $250 de propina, ¿me puedes hacer un depósito de $100 a una cuenta BBVA?"
→ ESTAFA. propina_falsa. Perpetrador: cliente. El repartidor es la víctima. risk_level: alto.
El cliente inventa una propina para convencer al repartidor de depositar dinero real de su bolsillo.

Ejemplo 6 — Cliente comparte número "123456789" y dice "Es bbva" después de pedir un depósito.
→ ESTAFA. propina_falsa / deposito_falso. Perpetrador: cliente. risk_level: alto.

Responde ÚNICAMENTE con JSON válido con exactamente estos campos (sin texto extra antes ni después):
{
  "risk_level": "alto|medio|bajo",
  "scam_type": "robo_otp|robo_codigo_entrega|propina_falsa|deposito_falso|redireccion_externa|cobro_externo|ninguno",
  "perpetrator": "cliente|repartidor|tendero|desconocido",
  "victim": "cliente|repartidor|ambos|desconocido",
  "evidence": "máximo 80 caracteres del fragmento que delata la estafa, o null si no hay",
  "reasoning": "máximo 120 caracteres explicando la decisión"
}"""


def _parse_response(raw: str) -> dict | None:
    """
    Extrae JSON del response de Gemini aunque venga con texto antes/después o truncado.
    """
    # Limpiar bloques de código markdown
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    # Intento 1: JSON completo
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Intento 2: extraer entre primer { y último }
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Intento 3: JSON truncado — cerrar manualmente y parsear lo que llegó
    if start != -1:
        fragment = cleaned[start:]
        # Cerrar llaves abiertas y comillas sin cerrar
        open_braces = fragment.count('{') - fragment.count('}')
        if fragment.rstrip().endswith(','):
            fragment = fragment.rstrip()[:-1]   # quitar coma trailing
        fragment += '}' * open_braces
        try:
            result = json.loads(fragment)
            logger.warning('[llm_classifier] JSON truncado — se recuperaron campos parciales')
            return result
        except json.JSONDecodeError:
            pass

    return None


def classify(messages: List[Dict], rules_reasons: List[str]) -> Dict:
    """
    Invoca a Gemini para clasificar la conversación.

    Args:
        messages: lista de mensajes con 'role'/'sender' y 'content'/'text'
        rules_reasons: razones que activaron el motor de reglas (contexto adicional)

    Returns:
        dict con risk_level, scam_type, evidence, reasoning
    """
    conv_lines = []
    for m in messages:
        role = m.get('role') or m.get('sender', 'desconocido')
        text = m.get('content') or m.get('text', '')
        label = 'Usuario' if role in ('user', 'usuario') else 'Repartidor/Soporte'
        conv_lines.append(f"{label}: {text}")

    conversation_text = '\n'.join(conv_lines)
    rules_context = ', '.join(rules_reasons) if rules_reasons else 'ninguna'

    user_message = f"""Analiza esta conversación de entrega de Rappi:

---
{conversation_text}
---

Señales que activaron el pre-filtro automático: {rules_context}

Responde con JSON estricto como se especificó."""

    try:
        from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])
        raw = response.content.strip()
        logger.info(f"[llm_classifier] RAW Gemini: {raw[:200]}")

        result = _parse_response(raw)

        if result and 'risk_level' in result:
            # Validar valores permitidos
            if result.get('risk_level') not in ('alto', 'medio', 'bajo'):
                result['risk_level'] = 'medio'
            valid_scam_types = (
                'robo_otp', 'robo_codigo_entrega', 'propina_falsa',
                'deposito_falso', 'redireccion_externa', 'cobro_externo', 'ninguno'
            )
            if result.get('scam_type') not in valid_scam_types:
                result['scam_type'] = 'ninguno'
            if result.get('perpetrator') not in ('cliente', 'repartidor', 'tendero', 'desconocido'):
                result['perpetrator'] = 'desconocido'
            if result.get('victim') not in ('cliente', 'repartidor', 'ambos', 'desconocido'):
                result['victim'] = 'desconocido'
            return result

        logger.warning(f"[llm_classifier] No se pudo parsear JSON. Raw: {raw[:150]}")
        return {
            "risk_level": "medio",
            "scam_type": "ninguno",
            "evidence": None,
            "reasoning": f"Error de parseo: {raw[:80]}",
        }

    except Exception as e:
        logger.error(f"[llm_classifier] Error invocando Gemini: {e}")
        return {
            "risk_level": "medio",
            "scam_type": "ninguno",
            "evidence": None,
            "reasoning": f"Error Gemini: {e}",
        }
