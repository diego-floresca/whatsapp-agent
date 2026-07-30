"""
Capa 1 (nuevo): Triage LLM con Gemini Flash.
Reemplaza al motor de reglas regex.

En vez de regex frágiles que pierden variantes lingüísticas, hace una pregunta
binaria a Gemini con un prompt mínimo (~100 tokens de entrada):

    ¿Hay señal de fraude en esta conversación? → SI / NO

Si la respuesta es SI, firestore_listener invoca llm_classifier para el análisis completo.
Si es NO, termina ahí. Costo total por conversación sin fraude: ~$0.000008.

Ventaja vs regex: entiende lenguaje natural, regionalismos, errores de ortografía
y cualquier variante que un regex nunca cubriría.
"""

import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from langchain_google_vertexai import ChatVertexAI  # noqa: PLC0415
        project = os.environ.get('PROJECT_ID', 'lunatic-analytics')
        _llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            temperature=0.0,
            max_output_tokens=200,  # Gemini 2.5 Flash usa thinking tokens — necesita margen
            project=project,
            location="us-central1",
        )
    return _llm


_TRIAGE_PROMPT = """Eres un detector de fraude en conversaciones de delivery (Rappi, México/Latam).
Analiza esta conversación y responde ÚNICAMENTE con SI o NO.

¿Hay alguna señal de posible fraude, estafa o comportamiento sospechoso?

Señales que debes detectar (de cualquier participante):
- Solicitudes de depósito, transferencia o pago fuera de la app
- Promesas de propina a cambio de favores financieros al repartidor
- Solicitudes de códigos OTP, de verificación o de entrega
- Números de cuenta bancaria compartidos en el chat
- Redirección a otro WhatsApp o número personal como "soporte oficial"
- Suplantación de soporte de Rappi
- Cobros fuera de la app por parte del tendero o repartidor

Responde solo con una palabra: SI o NO"""


def check(messages: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Triage binario con Gemini Flash.
    Envía toda la conversación para evaluar el contexto completo.

    Returns:
        (triggered: bool, reasons: list[str])
    """
    if not messages:
        return False, []

    lines = []
    for m in messages:
        role = m.get('role') or m.get('sender', 'desconocido')
        text = m.get('content') or m.get('text', '')
        label = 'Cliente' if role in ('user', 'usuario', 'cliente') else 'Agente'
        lines.append(f"{label}: {text}")

    conversation_text = '\n'.join(lines)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
        response = _get_llm().invoke([
            SystemMessage(content=_TRIAGE_PROMPT),
            HumanMessage(content=conversation_text),
        ])
        answer = response.content.strip().upper()
        print(f'[triage] Gemini respondió: {answer!r}')  # visible siempre en terminal

        triggered = 'SI' in answer or 'SÍ' in answer or answer.startswith('S')
        reasons = ['triage_llm:sospechoso'] if triggered else []
        return triggered, reasons

    except Exception as e:
        logger.error(f"[triage] Error en triage Gemini: {e}")
        # Fallback conservador: no disparar para evitar falsos positivos por error
        return False, []
