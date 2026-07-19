import { useEffect, useRef, useState, type FormEvent } from 'react';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../types';

interface Props {
  messages: Message[];
  loading: boolean;
  sending: boolean;
  error: string | null;
  aiEnabled: boolean;
  onSend: (content: string) => Promise<void>;
}

export function ChatWindow({ messages, loading, sending, error, aiEnabled, onSend }: Props) {
  const [text, setText] = useState('');
  const [sendError, setSendError] = useState<string | null>(null);
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

  return (
    <>
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
