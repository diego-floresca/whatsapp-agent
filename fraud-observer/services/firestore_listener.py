"""
Listener de Firestore en tiempo real.

Escucha cambios en la colección 'users' (mismo patrón que subscribeToUsers en TS).
Cuando last_interaction cambia (nuevo mensaje), corre el pipeline completo:
  reglas → [LLM si aplica] → scorer → escribe fraud_scores/{waId} → [SMS si umbral]
"""

import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

from google.cloud import firestore
from google.cloud.firestore_v1.watch import DocumentChange

from services.triage import check as triage_check
from services.llm_classifier import classify
from services.risk_scorer import compute as score_compute, should_alert
from services.twilio_alert import send_alert

# ── Firestore client (singleton, mismo patrón que firestore_service.py) ──────
_db: firestore.Client | None = None


def init_db() -> firestore.Client:
    global _db
    if _db is None:
        project = os.environ.get('PROJECT_ID')
        database = os.environ.get('DATABASE_NAME', '(default)')
        _db = firestore.Client(project=project, database=database)
        print(f'✅ Firestore conectado — project: {project} db: {database}')
    return _db


def _get_db() -> firestore.Client:
    if _db is None:
        raise RuntimeError('Llama init_db() antes de usar el listener')
    return _db


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fetch_messages(wa_id: str) -> List[Dict]:
    """Recupera todos los mensajes de una conversación, ordenados cronológicamente."""
    db = _get_db()
    docs = (
        db.collection('users')
        .document(wa_id)
        .collection('messages')
        .order_by('timestamp', direction=firestore.Query.ASCENDING)
        .stream()
    )
    msgs = []
    for doc in docs:
        data = doc.to_dict()
        msgs.append({
            'role': data.get('role', 'unknown'),
            'content': data.get('content', ''),
            'type': data.get('type', 'text'),
        })
    return msgs


def _write_fraud_score(wa_id: str, score: float, risk_level: str, llm_result: Dict | None) -> None:
    """
    Escribe fraud_scores/{waId} en dos pasos:
    1. set() — sobreescribe todos los campos del análisis actual
    2. update() — actualiza max_score SOLO si el nuevo score es mayor al existente
    Separar los dos pasos evita que max_score dependa de leer-y-escribir en un solo
    payload donde un read stale podría pisar el valor correcto.

    Si score=0 y no existe documento previo, no se crea — no hay historial que preservar.
    Si score=0 y ya existe documento, sí se actualiza el score actual a 0 (max_score se preserva).
    """
    db = _get_db()
    ref = db.collection('fraud_scores').document(wa_id)

    # Paso 1: leer estado previo
    existing = ref.get()
    existing_data = existing.to_dict() if existing.exists else {}

    # Si score=0 y no hay historial, no crear documento vacío
    if score == 0.0 and not existing.exists:
        print(f'[observer] Score=0 sin historial previo — no se crea documento')
        return

    already_alerted = existing_data.get('alerted', False)
    prev_max = existing_data.get('max_score', 0.0)

    # Paso 2: escribir todos los campos del análisis actual
    payload: Dict[str, Any] = {
        'score': score,
        'max_score': prev_max,          # se actualiza en paso 3 si corresponde
        'risk_level': risk_level,
        'scam_type': llm_result.get('scam_type') if llm_result else 'ninguno',
        'evidence': llm_result.get('evidence') if llm_result else None,
        'reasoning': llm_result.get('reasoning') if llm_result else None,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'alerted': already_alerted,
    }
    ref.set(payload)

    # Paso 3: actualizar max_score SOLO si el score actual lo supera
    if score > prev_max:
        ref.update({'max_score': score})
        print(f'[observer] max_score actualizado: {prev_max:.2f} → {score:.2f}')
    else:
        print(f'[observer] max_score preservado: {prev_max:.2f} (score actual {score:.2f} no lo supera)')


def _mark_alerted(wa_id: str) -> None:
    db = _get_db()
    db.collection('fraud_scores').document(wa_id).update({'alerted': True})


# ── Pipeline principal ────────────────────────────────────────────────────────

def process_conversation(wa_id: str) -> None:
    """Corre el pipeline completo para una conversación."""
    print(f'[observer] Analizando conversación: {wa_id}')

    messages = _fetch_messages(wa_id)
    if not messages:
        return

    # Capa 1: triage LLM (Gemini Flash, prompt mínimo — reemplaza regex)
    triggered, reasons = triage_check(messages)
    print(f'[observer] Triage: triggered={triggered}')

    # Capa 2: clasificación completa (solo si triage detectó sospecha)
    llm_result = None
    if triggered:
        llm_result = classify(messages, reasons)
        print(f'[observer] Clasificación: {llm_result}')

    # Score final
    score, risk_level = score_compute(triggered, reasons, llm_result)
    print(f'[observer] Score={score:.2f} risk_level={risk_level}')

    # Siempre intentar escribir — _write_fraud_score decide si crear o actualizar
    # según si ya existe historial previo. Esto permite que el score baje a 0
    # cuando mensajes posteriores son inocentes, manteniendo max_score intacto.
    _write_fraud_score(wa_id, score, risk_level, llm_result)

    # Alerta SMS si cruza el umbral y no se ha alertado antes
    if should_alert(score):
        db = _get_db()
        doc = db.collection('fraud_scores').document(wa_id).get()
        already_alerted = doc.to_dict().get('alerted', False) if doc.exists else False

        if not already_alerted:
            scam_type = llm_result.get('scam_type') if llm_result else None
            sent = send_alert(wa_id, scam_type)
            if sent:
                _mark_alerted(wa_id)


# ── Listener Firestore ────────────────────────────────────────────────────────

_initialized = threading.Event()
_init_lock = threading.Lock()
_first_snapshot_done = False


def _on_users_snapshot(col_snapshot, changes: List[DocumentChange], read_time) -> None:
    """
    Callback del listener en la colección 'users'.
    Primera llamada: carga inicial de todos los usuarios existentes — se ignora.
    Llamadas siguientes: procesa usuarios modificados (nuevo mensaje recibido).
    """
    global _first_snapshot_done

    with _init_lock:
        if not _first_snapshot_done:
            _first_snapshot_done = True
            print(f'[observer] Snapshot inicial: {len(changes)} usuarios existentes — ignorando')
            _initialized.set()
            return

    for change in changes:
        if change.type.name in ('MODIFIED', 'ADDED'):
            wa_id = change.document.id
            # Procesamos en hilo separado para no bloquear el callback de Firestore
            threading.Thread(target=process_conversation, args=(wa_id,), daemon=True).start()


def start_listener() -> None:
    """
    Inicia el listener en la colección 'users'.
    Bloqueante: mantiene el hilo principal vivo.
    """
    db = _get_db()
    print('[observer] Iniciando listener en colección "users"...')
    unsubscribe = db.collection('users').on_snapshot(_on_users_snapshot)

    # Esperar a que el snapshot inicial termine antes de anunciar que estamos listos
    _initialized.wait(timeout=10)
    print('[observer] ✅ Listener activo — esperando mensajes nuevos...')

    try:
        threading.Event().wait()  # Mantener vivo indefinidamente
    except KeyboardInterrupt:
        print('[observer] Deteniendo listener...')
        unsubscribe()
