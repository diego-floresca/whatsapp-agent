import { useEffect, useRef, useState, type FormEvent } from 'react';
import { MessageBubble } from './MessageBubble';
import type { Message, FraudScore } from '../types';

const SCAM_LABELS: Record<string, string> = {
  robo_otp:             'Robo de código OTP',
  robo_codigo_entrega:  'Robo de código de entrega',
  deposito_falso:       'Depósito / transferencia falsa',
  redireccion_externa:  'Redirección a canal externo',
  ninguno:              'Sin tipo definido',
};

interface Props {
  messages: Message[];
  loading: boolean;
  sending: boolean;
  error: string | null;
  aiEnabled: boolean;
  onSend: (content: string) => Promise<void>;
  fraudScore?: FraudScore | null;
}

export function ChatWindow({ messages, loading, sending, error, aiEnabled, onSend, fraudScore }: Props) {
  const [text, setText] = useState('');
  const [sendError, setSendError] = useState<string | null>(null);
  const [fraudPanelOpen, setFraudPanelOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll automático al último mensaje
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const content = text.trim();
    if (!content || sending) return;

    setSendError(null);
    setText('');
    try {
      await onSend(content);
    } catch (err) {
      setSendError(err instanceof Error ? err.message : 'Error al enviar');
      setText(content); // Restaurar texto si falló
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-gray-600 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    );
  }

  const showFraudAlert = fraudScore && fraudScore.risk_level === 'alto';
  const showFraudWarning = fraudScore && fraudScore.risk_level === 'medio';

  return (
    <>
      {/* Panel de alerta de fraude */}
      {(showFraudAlert || showFraudWarning) && (
        <div
          className={`shrink-0 border-b mx-0 ${
            showFraudAlert
              ? 'bg-red-950/50 border-red-800/60'
              : 'bg-yellow-950/40 border-yellow-800/50'
          }`}
        >
          <button
            onClick={() => setFraudPanelOpen((v) => !v)}
            className={`w-full flex items-center justify-between px-4 py-2 text-xs font-semibold ${
              showFraudAlert ? 'text-red-300' : 'text-yellow-300'
            }`}
          >
            <span className="flex items-center gap-2">
              <span>{showFraudAlert ? '🚨' : '⚠️'}</span>
              <span>
                {showFraudAlert
                  ? `ALERTA DE FRAUDE — ${SCAM_LABELS[fraudScore.scam_type ?? 'ninguno'] ?? fraudScore.scam_type}`
                  : `Posible riesgo — ${SCAM_LABELS[fraudScore!.scam_type ?? 'ninguno'] ?? fraudScore!.scam_type}`}
              </span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                showFraudAlert ? 'bg-red-700 text-red-100' : 'bg-yellow-700 text-yellow-100'
              }`}>
                Score {((fraudScore?.score ?? 0) * 100).toFixed(0)}%
              </span>
            </span>
            <span className="text-gray-500">{fraudPanelOpen ? '▲' : '▼'}</span>
          </button>

          {fraudPanelOpen && (
            <div className="px-4 pb-3 space-y-1.5">
              {fraudScore?.evidence && (
                <div>
                  <span className="text-[10px] uppercase tracking-wide text-gray-500 font-medium">Evidencia detectada</span>
                  <blockquote className={`mt-1 pl-2 border-l-2 text-xs italic ${
                    showFraudAlert ? 'border-red-600 text-red-200' : 'border-yellow-600 text-yellow-200'
                  }`}>
                    "{fraudScore.evidence}"
                  </blockquote>
                </div>
              )}
              {fraudScore?.reasoning && (
                <div>
                  <span className="text-[10px] uppercase tracking-wide text-gray-500 font-medium">Razonamiento</span>
                  <p className="mt-0.5 text-xs text-gray-400">{fraudScore.reasoning}</p>
                </div>
              )}
              {fraudScore?.alerted && (
                <p className="text-[10px] text-green-400 flex items-center gap-1">
                  <span>✓</span> SMS de alerta enviado al usuario
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Mensajes */}
      <div className="flex-1 overflow-y-auto py-3 flex flex-col gap-0.5">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-600 text-sm">
            Sin mensajes aún
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Errores */}
      {(error || sendError) && (
        <div className="px-4 py-2 text-xs text-red-400 bg-red-900/10 border-t border-red-900/20">
          {error ?? sendError}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-[#1e1e1e] bg-[#141414] px-4 py-3 shrink-0">
        {!aiEnabled ? (
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Escribe un mensaje como agente..."
              disabled={sending}
              className="
                flex-1 rounded-lg bg-[#1e1e1e] border border-[#2a2a2a]
                px-3 py-2 text-sm text-gray-100 placeholder-gray-600
                focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                disabled:opacity-50 transition-colors
              "
            />
            <button
              type="submit"
              disabled={!text.trim() || sending}
              className="
                px-4 py-2 rounded-lg bg-orange-600 text-white text-sm font-medium
                hover:bg-orange-500 disabled:opacity-40 disabled:cursor-not-allowed
                transition-colors shrink-0
              "
            >
              {sending ? 'Enviando…' : 'Enviar'}
            </button>
          </form>
        ) : (
          <div className="flex items-center justify-center text-xs text-gray-600 py-1">
            La IA está respondiendo — desactiva el toggle para tomar control
          </div>
        )}
      </div>
    </>
  );
}
