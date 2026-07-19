import { useState } from 'react';
import { toggleAI } from '../api/client';
import type { Conversation } from '../types';

interface Props {
  conversation: Conversation;
  onAIToggled: (enabled: boolean) => void;
}

export function ChatHeader({ conversation, onAIToggled }: Props) {
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleToggle() {
    const next = !conversation.ai_enabled;
    setToggling(true);
    setError(null);
    try {
      await toggleAI(conversation.waId, next);
      onAIToggled(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cambiar IA');
    } finally {
      setToggling(false);
    }
  }

  return (
    <div className="flex items-center justify-between px-5 py-3 border-b border-[#1e1e1e] bg-[#141414] shrink-0">
      {/* Nombre y teléfono */}
      <div>
        <h2 className="text-sm font-semibold text-gray-100">{conversation.name}</h2>
        <p className="text-xs text-gray-500">{conversation.phone_number}</p>
      </div>

      {/* Toggle IA */}
      <div className="flex items-center gap-3">
        {error && (
          <span className="text-xs text-red-400">{error}</span>
        )}

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {conversation.ai_enabled ? 'IA activa' : 'Agente humano'}
          </span>
          <button
            onClick={handleToggle}
            disabled={toggling}
            title={conversation.ai_enabled ? 'Desactivar IA' : 'Activar IA'}
            className={`
              relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center
              rounded-full transition-colors duration-200 focus:outline-none
              disabled:opacity-50
              ${conversation.ai_enabled ? 'bg-blue-600' : 'bg-gray-600'}
            `}
          >
            <span
              className={`
                inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform duration-200
                ${conversation.ai_enabled ? 'translate-x-4' : 'translate-x-1'}
              `}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
