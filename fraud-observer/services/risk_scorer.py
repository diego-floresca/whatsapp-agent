"""
Combina la salida del motor de reglas y del LLM en un score 0.0–1.0.

Lógica:
  - Sin reglas disparadas              → 0.0   (LLM no se invocó)
  - Reglas disparadas + LLM "bajo"     → 0.35  (falso positivo probable)
  - Reglas disparadas + LLM "medio"    → 0.65
  - Reglas disparadas + LLM "alto"     → 0.90
  - Reglas disparadas + LLM falló      → 0.55  (conservador)

Umbral por defecto: RISK_THRESHOLD=0.7 en .env
"""

import os
from typing import Dict, List, Optional, Tuple

_SCORE_MAP = {
    'bajo': 0.35,
    'medio': 0.65,
    'alto': 0.90,
}

_RULES_ONLY_SCORE = 0.55  # si LLM falló


def compute(
    rules_triggered: bool,
    rules_reasons: List[str],
    llm_result: Optional[Dict],
) -> Tuple[float, str]:
    """
    Calcula el score final y el nivel de riesgo legible.

    Returns:
        (score: float, risk_label: str)  — risk_label: 'bajo'|'medio'|'alto'
    """
    if not rules_triggered:
        return 0.0, 'bajo'

    if llm_result is None:
        return _RULES_ONLY_SCORE, 'medio'

    llm_level = llm_result.get('risk_level', 'medio')
    score = _SCORE_MAP.get(llm_level, _RULES_ONLY_SCORE)
    return score, llm_level


def should_alert(score: float) -> bool:
    threshold = float(os.environ.get('RISK_THRESHOLD', '0.7'))
    return score >= threshold
