import type { Message } from '../types';

interface Props {
  message: Message;
}

const ROLE_STYLES = {
  user: {
    wrapper: 'justify-start',
    bubble: 'bg-[#1e1e1e] text-gray-200 rounded-tl-none',
    label: 'text-gray-500',
  },
  ai: {
    wrapper: 'justify-end',
    bubble: 'bg-blue-600 text-white rounded-tr-none',
    label: 'text-blue-300',
  },
  human: {
    wrapper: 'justify-end',
    bubble: 'bg-orange-600 text-white rounded-tr-none',
    label: 'text-orange-300',
  },
} as const;

const ROLE_LABELS: Record<Message['role'], string> = {
  user: 'Cliente',
  ai: 'IA',
  human: 'Agente',
};

function formatTime(iso: string | null): string {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('es-MX', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function MessageBubble({ message }: Props) {
  const style = ROLE_STYLES[message.role] ?? ROLE_STYLES.user;

  const isMedia =
    message.content.startsWith('[AUDIO') || message.content.startsWith('[IMAGEN');

  return (
    <div className={`flex ${style.wrapper} px-4 py-1`}>
      <div className="max-w-[72%] flex flex-col gap-0.5">
        <div className={`rounded-xl px-3 py-2 text-sm leading-relaxed ${style.bubble}`}>
          {isMedia ? (
            <span className="italic opacity-75">{message.content}</span>
          ) : (
            message.content
          )}
        </div>
        <div className={`flex gap-2 text-[10px] ${style.label} ${message.role !== 'user' ? 'justify-end' : ''}`}>
          <span>{ROLE_LABELS[message.role]}</span>
          <span>{formatTime(message.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}
