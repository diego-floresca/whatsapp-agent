# Sherlock Chat — Contexto para Claude

Proyecto de detección de fraude en conversaciones de WhatsApp para demo de entrevista AI Engineer en Rappi.

---

## Estructura del repo

```
whatsapp-agent/
├── fraud-observer/          # Servicio Python — detecta fraude en tiempo real
├── whatsapp-interface/
│   ├── backend/             # Express + TypeScript — webhook Meta, API REST, SSE
│   └── frontend/            # React + Vite + Tailwind — dashboard de conversaciones
└── whatsapp-bot/            # Bot original de Parco (NO tocar, está en desuso)
```

---

## Cómo levantar el proyecto

### 1. Backend (Express)
```bash
cd whatsapp-interface/backend
npm run dev
# Corre en puerto 3001
```

### 2. Frontend (React)
```bash
cd whatsapp-interface/frontend
npm run dev
# Corre en puerto 5174
```

### 3. Tunnel para webhook de Meta
```bash
ngrok http 3001
# URL resultante → configurar en Meta for Developers como:
# https://xxx.ngrok-free.app/webhook
# Verify token: BosEn_tka0_QTFKYr_Pe4w
```

### 4. fraud-observer
```bash
cd fraud-observer
source venv_fraud/bin/activate
python main.py
```

---

## Flujo de datos

```
WhatsApp → Meta API → POST /webhook (Express)
                           ↓
                      Firestore: users/{waId}/messages
                           ↓
                   fraud-observer escucha cambios
                           ↓
              triage.py (Gemini Flash — SI/NO)
                           ↓ SI
              llm_classifier.py (análisis completo)
                           ↓
              risk_scorer.py (score 0.0–1.0)
                           ↓
              fraud_scores/{waId} en Firestore
                     ↓              ↓
             SSE → dashboard    SMS Twilio (si score > 0.7)
```

---

## Firestore — colecciones

### `users/{waId}`
```
name, phone_number, ai_enabled, status, created_at, last_interaction
  └── messages/  (subcollección)
        role: 'user' | 'human' | 'ai'
        content, type, timestamp
```

### `fraud_scores/{waId}`
```
score          # riesgo actual (0.0–1.0), sube y baja con cada mensaje
max_score      # pico histórico, NUNCA baja — regla: solo se actualiza si score > max_score
risk_level     # 'bajo' | 'medio' | 'alto'
scam_type      # tipo de fraude (ver abajo)
perpetrator    # 'cliente' | 'repartidor' | 'tendero' | 'desconocido'
victim         # 'cliente' | 'repartidor' | 'ambos' | 'desconocido'
evidence       # fragmento textual de la conversación que delató el fraude
reasoning      # explicación breve del modelo
alerted        # bool — si ya se envió SMS (no se repite)
updated_at
```

---

## fraud-observer — detalle de cada archivo

### `services/triage.py` ← CAPA 1 (actual)
Pregunta binaria a Gemini Flash: "¿hay fraude? SI/NO"
- Solo envía los últimos 10 mensajes (costo mínimo)
- `max_output_tokens=200` — necesita margen por thinking tokens de Gemini 2.5 Flash
- Si NO → pipeline termina, score=0, documento existente se preserva
- Si SI → llama a llm_classifier

**Historia:** antes existía `services/rules_engine.py` (v1) con 10 regex. Se reemplazó porque perdía variantes lingüísticas ("depositarme" vs "deposítame"). El archivo se conserva como referencia de la evolución.

### `services/llm_classifier.py` ← CAPA 2
Análisis completo con Gemini 2.5 Flash.
- `max_output_tokens=8192` — Gemini 2.5 Flash consume tokens de thinking antes de responder; con menos tokens el JSON se truncaba a mitad del campo `perpetrator`
- Prompt con few-shot de 6 ejemplos (3 legítimos, 3 fraudes)
- Retorna JSON: `risk_level`, `scam_type`, `perpetrator`, `victim`, `evidence`, `reasoning`
- `_parse_response()` tiene 3 intentos: JSON completo → extraer entre `{}` → reparar JSON truncado

### `services/risk_scorer.py`
Convierte el resultado del LLM en número:
- `triggered=False` → 0.0
- LLM falló → 0.55
- LLM bajo → 0.35
- LLM medio → 0.65
- LLM alto → 0.90

### `services/firestore_listener.py`
- Escucha `users/` collection con `on_snapshot`
- Ignora el snapshot inicial (evita re-procesar conversaciones existentes al arrancar)
- Lanza `process_conversation(wa_id)` en thread separado por cada cambio
- `_write_fraud_score()` usa dos pasos: `ref.set(payload)` + `ref.update({'max_score': score})` solo si `score > prev_max`
- Si `score == 0.0` → NO escribe (preserva documento existente con max_score previo)

### `services/twilio_alert.py`
SMS al número del usuario si score > `RISK_THRESHOLD` (default 0.7).
Número Twilio: `+16204140329`
Credenciales pendientes: `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN` en `fraud-observer/.env`

### `services/rules_engine.py` ← CAPA 1 v1 (legacy, no se usa)
10 patrones regex. Se conserva como referencia. Cubre:
- robo OTP, código de entrega anticipado
- propina falsa (cliente → repartidor): `_FAKE_TIP` + `_DEPOSIT_REQUEST`
- número de cuenta bancaria expuesto: `_BANK_ACCOUNT_NUMBER` (8-18 dígitos) + `_BANK_NAME`
- pago en efectivo externo: `_CASH_CHANNEL` (oxxo, 7-eleven...) + `_DEPOSIT_REQUEST`
- cobro externo del tendero: `_OVERCHARGE`
- redirección a canal externo, falso soporte

### `demo_replay.py`
Replay de conversación de fraude para demos. `--wa-id` para elegir número destino.

### `disable_ai.py`
Desactiva/reactiva la IA para usuarios. `--all` o `--wa-id`. `--enable` para reactivar.

### `data/synthetic_conversations.json`
80 conversaciones sintéticas: 30 fraudes, 30 negativos difíciles, 20 neutrales.

### `eval/evaluate.py`
Evaluación formal: split 70/30, P/R/F1, matriz de confusión, costo de FN=$180 y FP=$5.

---

## Tipos de fraude (`scam_type`)

| Tipo | Quién defrauda | A quién |
|---|---|---|
| `robo_otp` | Repartidor | Cliente |
| `robo_codigo_entrega` | Repartidor | Cliente/plataforma |
| `propina_falsa` | Cliente | Repartidor |
| `deposito_falso` | Cualquiera | Cualquiera |
| `redireccion_externa` | Repartidor | Cliente |
| `cobro_externo` | Tendero | Cliente/plataforma |
| `ninguno` | — | — |

---

## Backend — rutas principales

```
GET  /api/conversations/stream          SSE — eventos 'update' y 'fraud_update'
GET  /api/conversations/                lista de conversaciones
GET  /api/conversations/fraud-scores    todos los fraud_scores (carga inicial)
GET  /api/conversations/:waId/messages  mensajes de una conversación
POST /api/conversations/:waId/send      enviar mensaje como agente humano
PATCH /api/conversations/:waId/ai-toggle  activar/desactivar IA
GET  /webhook                           verificación Meta (hub.challenge)
POST /webhook                           recepción de mensajes WhatsApp
```

---

## Frontend — hooks principales

- `useConversations` — lista de conversaciones + SSE para actualizaciones
- `useMessages(waId)` — mensajes de la conversación activa + SSE para nuevos mensajes
- `useFraudScores` — carga inicial de fraud_scores + SSE para `fraud_update`

El SSE usa `EventSource` a `/api/conversations/stream`. Eventos: `update` (conversaciones) y `fraud_update` (scores de fraude).

---

## Variables de entorno

### `whatsapp-interface/backend/.env`
```
PORT=3001
WEBHOOK_VERIFY_TOKEN=BosEn_tka0_QTFKYr_Pe4w
META_ACCESS_TOKEN=...
PHONE_NUMBER_ID=959889483881739
DATABASE_NAME=agent-whatsapp-chats-database
GOOGLE_CLOUD_PROJECT=lunatic-analytics
```

### `fraud-observer/.env`
```
PROJECT_ID=lunatic-analytics
DATABASE_NAME=agent-whatsapp-chats-database
TWILIO_ACCOUNT_SID=PENDIENTE
TWILIO_AUTH_TOKEN=PENDIENTE
TWILIO_FROM_NUMBER=+16204140329
RISK_THRESHOLD=0.7
```

---

## Credenciales GCP
Se usan ADC (Application Default Credentials) vía `gcloud auth application-default login`.
No hay API keys en el código. Firestore y Vertex AI comparten las mismas credenciales.
Proyecto GCP: `lunatic-analytics`

---

## Decisiones de arquitectura importantes

1. **Cloud Run eliminado** — el bot original de Parco estaba en Cloud Run y seguía respondiendo mensajes aunque se desactivara la IA en Firestore. Se borró el servicio. El webhook ahora vive en el Express backend local con ngrok.

2. **Mensajes guardados ANTES de actualizar last_interaction** — el listener SSE dispara cuando cambia `last_interaction`. Si se actualizaba primero y el mensaje aún no estaba escrito, el frontend hacía fetch y no encontraba el mensaje nuevo. El orden correcto: guardar mensaje → actualizar last_interaction.

3. **max_score en dos pasos** — se intentó con transacción Firestore pero era complejo. La solución actual: `ref.set(payload)` con el `prev_max` leído antes, seguido de `ref.update({'max_score': score})` solo si `score > prev_max`. Simple y funciona.

4. **No escribir cuando score=0** — si el triage dice NO, no se sobreescribe el documento de fraud_scores. Así el max_score de una conversación que ya tenía riesgo no se pierde cuando llegan mensajes inocentes después.

5. **Gemini 2.5 Flash necesita tokens generosos** — es un modelo de thinking. Usa tokens internos de razonamiento antes de escribir la respuesta. Con `max_output_tokens` pequeño el JSON se truncaba. Triage usa 200, clasificador usa 8192.

6. **ngrok sobre localtunnel** — localtunnel tiene una pantalla de bypass que Meta no puede pasar. ngrok no tiene esa restricción.
