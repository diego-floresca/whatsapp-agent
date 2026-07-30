"""
Fase 8 — Evaluación del pipeline completo sobre el dataset sintético.

Uso:
    cd fraud-observer
    python -m eval.evaluate

Requiere ANTHROPIC_API_KEY en .env o en el entorno.
Imprime precision, recall, F1 por tipo de estafa, matriz de confusión
y estimación de costo de negocio.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Añadir raíz al path para imports locales
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rules_engine import check as rules_check
from services.llm_classifier import classify
from services.risk_scorer import compute as score_compute, should_alert

# ── Configuración ─────────────────────────────────────────────────────────────

DATA_PATH = Path(__file__).parent.parent / 'data' / 'synthetic_conversations.json'
TEST_SPLIT = 0.30  # 30% para test

# Costo ilustrativo por error (en USD, orden de magnitud)
# Fuente: estimación propia inspirada en la función de pérdida asimétrica
# publicada por el equipo de fraude de Rappi (arXiv 2111.03707).
# ESTAS CIFRAS SON ILUSTRATIVAS, no son datos reales de Rappi.
COST_FALSE_NEGATIVE = 180.0   # Estafa no detectada: pérdida promedio por víctima
COST_FALSE_POSITIVE = 5.0     # Falsa alarma: fricción/interrupción de conversación legítima


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_pipeline(messages: list) -> tuple[bool, str]:
    """
    Corre el pipeline completo en una conversación.
    Retorna (is_fraud_detected, scam_type_predicted).
    """
    triggered, reasons = rules_check(messages)

    llm_result = None
    if triggered:
        llm_result = classify(messages, reasons)

    score, _ = score_compute(triggered, reasons, llm_result)
    detected = should_alert(score)

    scam_type = 'ninguno'
    if llm_result:
        scam_type = llm_result.get('scam_type', 'ninguno')

    return detected, scam_type


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with open(DATA_PATH) as f:
        dataset = json.load(f)

    # Split 70/30 (determinista por posición, no temporal ya que es sintético)
    n = len(dataset)
    n_test = int(n * TEST_SPLIT)
    test_set = dataset[n - n_test:]

    print(f'Dataset total: {n} conversaciones')
    print(f'Set de prueba: {len(test_set)} conversaciones\n')

    # Métricas globales binarias
    tp = fp = fn = tn = 0

    # Métricas por tipo de estafa
    per_type: dict[str, dict] = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})

    # Para matriz de confusión: pred vs real
    confusion: dict[tuple, int] = defaultdict(int)

    # Costo acumulado
    total_cost = 0.0

    for conv in test_set:
        true_label = conv['label']        # 'estafa' | 'legitima' | 'neutral'
        true_type = conv['scam_type']     # str | null
        is_true_fraud = true_label == 'estafa'

        detected, pred_type = run_pipeline(conv['messages'])

        # Matriz de confusión simplificada
        confusion[(true_label, 'detectada' if detected else 'no_detectada')] += 1

        if is_true_fraud and detected:
            tp += 1
            per_type[true_type]['tp'] += 1
        elif not is_true_fraud and detected:
            fp += 1
            total_cost += COST_FALSE_POSITIVE
        elif is_true_fraud and not detected:
            fn += 1
            total_cost += COST_FALSE_NEGATIVE
            per_type[true_type]['fn'] += 1
        else:
            tn += 1

    # ── Reporte ───────────────────────────────────────────────────────────────

    print('=' * 60)
    print('RESULTADOS GLOBALES (detección binaria)')
    print('=' * 60)
    p, r, f1 = precision_recall_f1(tp, fp, fn)
    print(f'  TP: {tp}  FP: {fp}  FN: {fn}  TN: {tn}')
    print(f'  Precision : {p:.3f}')
    print(f'  Recall    : {r:.3f}')
    print(f'  F1        : {f1:.3f}')

    print()
    print('=' * 60)
    print('MÉTRICAS POR TIPO DE ESTAFA')
    print('=' * 60)
    scam_types = ['robo_otp', 'robo_codigo_entrega', 'deposito_falso', 'redireccion_externa']
    for st in scam_types:
        m = per_type[st]
        tp_t, fn_t = m['tp'], m['fn']
        recall_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
        print(f'  {st:<25} TP={tp_t} FN={fn_t} Recall={recall_t:.2f}')

    print()
    print('=' * 60)
    print('MATRIZ DE CONFUSIÓN (real vs predicción)')
    print('=' * 60)
    labels = ['estafa', 'legitima', 'neutral']
    preds = ['detectada', 'no_detectada']
    header = f"{'':15}" + ''.join(f'{p:>15}' for p in preds)
    print(header)
    for l in labels:
        row = f'{l:<15}' + ''.join(f'{confusion[(l, p)]:>15}' for p in preds)
        print(row)

    print()
    print('=' * 60)
    print('COSTO ESTIMADO DE NEGOCIO (cifras ilustrativas*)')
    print('=' * 60)
    fn_cost = fn * COST_FALSE_NEGATIVE
    fp_cost = fp * COST_FALSE_POSITIVE
    print(f'  Falsos negativos: {fn} × ${COST_FALSE_NEGATIVE:.0f} = ${fn_cost:.0f}')
    print(f'  Falsos positivos: {fp} × ${COST_FALSE_POSITIVE:.0f}  = ${fp_cost:.0f}')
    print(f'  Costo total estimado: ${total_cost:.0f}')
    print()
    print('  * Cifras ilustrativas de orden de magnitud para demostrar la metodología')
    print('    de pérdida asimétrica. No son datos reales de Rappi.')
    print('    Metodología inspirada en: arXiv 2111.03707 (Rappi Fraud Detection).')


if __name__ == '__main__':
    main()
