"""
Capa 1: Motor de reglas basado en regex/keywords.
Filtro barato que decide si vale la pena invocar al LLM.

El fraude puede originarse desde cualquier participante:
  - REPARTIDOR → cliente  (robo de OTP, falso soporte, redirección externa)
  - CLIENTE    → repartidor  (scam de propina falsa, transferencia a cuenta)
  - TENDERO    → cliente/repartidor  (cobro fuera de la app, datos bancarios)

Retorna: (triggered: bool, reasons: list[str])
"""

import re
from typing import List, Tuple, Dict

# ── Patrones: fraude del REPARTIDOR / AGENTE → cliente ───────────────────────

# Robo de OTP / código de verificación
_OTP_CONTEXT = re.compile(
    r'c[oó]digo.{0,30}(lleg[oó]|envi[oó]|recibi|sms|correo|email|verif|comparte|d[ií]me|necesito|escr[ií]be|manda)',
    re.IGNORECASE
)
_OTP_SHARE = re.compile(
    r'(comparte|d[ií]me|env[ií]a|manda|lee|dica|proporciona).{0,25}c[oó]digo',
    re.IGNORECASE
)
_OTP_KEYWORDS = re.compile(
    r'\b(otp|verificaci[oó]n|autenticaci[oó]n|c[oó]digo\s+de\s+seguridad|c[oó]digo\s+de\s+verificaci[oó]n)\b',
    re.IGNORECASE
)

# Robo del código de entrega (pide el código ANTES de llegar)
_DELIVERY_CODE_EARLY = re.compile(
    r'(c[oó]digo|pin).{0,20}(entrega|pedido|paquete|confirmar|marcar|sistema)',
    re.IGNORECASE
)

# Redirección a canal externo con número diferente
_EXTERNAL_NUMBER = re.compile(
    r'(\+\d{7,15}|00\d{7,15})',
)
_REDIRECT_CHANNEL = re.compile(
    r'(escr[ií]beme\s+(?:al|por|a\s+este)|contacta[nm]e?\s+(?:al|en|por)|mi\s+whatsapp\s+(?:es|personal|real|oficial))',
    re.IGNORECASE
)

# Falso soporte / sistema caído
_FAKE_SUPPORT = re.compile(
    r'(plataforma\s+ca[ií]da|sistema\s+(no\s+funciona|ca[ií]do|falla)|solo\s+por\s+aqu[ií]\s+puedo|'
    r'soy\s+del\s+(equipo|soporte|equipo\s+de)\s+rappi|rappi\s+soporte|problema\s+con\s+tu\s+cuenta)',
    re.IGNORECASE
)

# ── Patrones: fraude del CLIENTE → repartidor ────────────────────────────────

# Scam de propina falsa: cliente dice "te dejo propina" y luego pide depósito/transferencia
_FAKE_TIP = re.compile(
    r'\b(prop(?:ina|s)|te\s+dej[eé]|dej[eé]\s+(?:un[a]?\s+)?prop)',
    re.IGNORECASE
)

# Solicitud de depósito a cuenta bancaria externa
# Cubre: deposítame, depositarme, depositar, depósito, hacer un depósito, transferencia, recarga
_DEPOSIT_REQUEST = re.compile(
    r'\b(dep[oó]sita(?:r)?(?:me)?|dep[oó]sito|transferen(?:cia)?|recarga|'
    r'me\s+(?:puede[sn]?|har[ií]as?)\s+(?:hacer|un)\s+(?:el\s+)?dep[oó]sito|'
    r'hacer\s+(?:el\s+)?(?:favor\s+de\s+)?dep[oó]sitar)\b',
    re.IGNORECASE
)

# Número de cuenta bancaria expuesto en el chat (8-18 dígitos consecutivos)
_BANK_ACCOUNT_NUMBER = re.compile(
    r'\b\d{8,18}\b'
)

# Banco mencionado explícitamente (contexto de transacción real)
_BANK_NAME = re.compile(
    r'\b(bbva|banamex|santander|banorte|hsbc|scotiabank|bancomer|azteca|spin|hey\s+banco|'
    r'bancolombia|nequi|daviplata|yappy|sinpe|nubank|mercadopago|clip)\b',
    re.IGNORECASE
)

# Canal de pago en efectivo fuera de la app
_CASH_CHANNEL = re.compile(
    r'\b(oxxo|seven\s*eleven|7-?eleven|coppel|elektra|farmacia|bodega\s+aurrer[aá]|walmart)\b',
    re.IGNORECASE
)

# ── Patrones: fraude del TENDERO → cliente / repartidor ──────────────────────

# Cobro fuera de la app / precio diferente al mostrado
_OVERCHARGE = re.compile(
    r'(p[áa]game?\s+(?:aqu[ií]|directo|en\s+efectivo|aparte|por\s+separado)|'
    r'cobra(?:r|mos)?\s+(?:aparte|extra|diferente|directo)|'
    r'precio\s+diferente|producto\s+(?:no\s+est[aá]|falt[oó]|no\s+ten[ií]a))',
    re.IGNORECASE
)


def check(messages: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Evalúa la conversación completa contra todas las reglas.
    Analiza mensajes de TODOS los participantes — el fraude puede venir de cualquier lado.

    Args:
        messages: lista de dicts con claves 'role'/'sender' y 'content'/'text'

    Returns:
        (triggered, reasons) donde reasons es la lista de reglas que dispararon
    """
    def _extract_text(m: Dict) -> str:
        return m.get('content') or m.get('text', '')

    def _is_agent(m: Dict) -> bool:
        return (
            m.get('role') in ('human', 'ai', 'repartidor')
            or m.get('sender') in ('repartidor', 'agente')
        )

    def _is_user(m: Dict) -> bool:
        return (
            m.get('role') == 'user'
            or m.get('sender') in ('usuario', 'cliente')
        )

    agent_msgs = [_extract_text(m) for m in messages if _is_agent(m)]
    user_msgs  = [_extract_text(m) for m in messages if _is_user(m)]
    full_text  = ' '.join(_extract_text(m) for m in messages)
    agent_text = ' '.join(agent_msgs)
    user_text  = ' '.join(user_msgs)

    reasons: List[str] = []

    # ── Fraude agente → cliente ───────────────────────────────────────────────
    if _OTP_CONTEXT.search(agent_text) or _OTP_SHARE.search(agent_text):
        reasons.append('robo_otp:agente_pide_codigo')

    if _OTP_KEYWORDS.search(agent_text):
        reasons.append('robo_otp:keyword_otp_en_agente')

    if _DELIVERY_CODE_EARLY.search(agent_text):
        reasons.append('robo_codigo_entrega:agente_pide_codigo')

    if _EXTERNAL_NUMBER.search(agent_text) or (
        _REDIRECT_CHANNEL.search(agent_text) and _EXTERNAL_NUMBER.search(full_text)
    ):
        reasons.append('redireccion_externa:numero_alterno_en_agente')

    if _FAKE_SUPPORT.search(agent_text):
        reasons.append('falso_soporte:keyword_soporte_en_agente')

    # ── Fraude cliente → repartidor ───────────────────────────────────────────
    # Scam de propina falsa: menciona propina Y pide depósito/transferencia
    if _FAKE_TIP.search(user_text) and _DEPOSIT_REQUEST.search(full_text):
        reasons.append('propina_falsa:cliente_pide_deposito_externo')

    # Número de cuenta bancaria compartido en el chat
    if _BANK_ACCOUNT_NUMBER.search(full_text) and _BANK_NAME.search(full_text):
        reasons.append('cuenta_bancaria_expuesta:numero+banco')

    # Pago en efectivo fuera de la app solicitado por el cliente
    if _CASH_CHANNEL.search(full_text) and _DEPOSIT_REQUEST.search(full_text):
        reasons.append('pago_externo:canal_efectivo+deposito')

    # ── Fraude tendero → participantes ────────────────────────────────────────
    if _OVERCHARGE.search(full_text):
        reasons.append('cobro_externo:tendero_cobra_fuera_app')

    return bool(reasons), reasons
