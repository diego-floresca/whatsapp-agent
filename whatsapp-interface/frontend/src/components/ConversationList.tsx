import type { Conversation } from '../types';

interface Props {
  conversations: Conversation[];
  loading: boolean;
  activeWaId: string | null;
  onSelect: (waId: string) => void;
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  en_curso: { label: 'En curso', color: 'bg-blue-500' },
  resuelto: { label: 'Resuelto', color: 'bg-green-500' },
  sin_resolver: { label: 'Sin resolver', color: 'bg-red-500' },
};

function formatTime(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  }
  if (diffDays === 1) return 'Ayer';
  if (diffDays < 7) return date.toLocaleDateString('es-MX', { weekday: 'short' });
  return date.toLocaleDateString('es-MX', { day: '2-digit', month: 'short' });
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

export function ConversationList({ conversations, loading, activeWaId, onSelect }: Props) {
  if (loading) {
    return (
      <div className="flex flex-col gap-1 p-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg bg-[#1e1e1e] h-16" />
        ))}
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-500 text-sm">
        Sin conversaciones
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-y-auto">
      {conversations.map((conv) => {
        const isActive = conv.waId === activeWaId;
        const badge = STATUS_BADGE[conv.status] ?? STATUS_BADGE['en_curso'];

        return (
          <button
            key={conv.waId}
            onClick={() => onSelect(conv.waId)}
            className={`
              flex items-center gap-3 px-4 py-3 text-left transition-colors
              border-l-2 cursor-pointer
              ${isActive
                ? 'bg-[#1e1e1e] border-blue-500'
                : 'border-transparent hover:bg-[#141414]'
              }
            `}
          >
            {/* Avatar */}
            <div className="shrink-0 w-9 h-9 rounded-full bg-[#2a2a2a] flex items-center justify-center text-xs font-semibold text-gray-300">
              {getInitials(conv.name)}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-gray-100 truncate">{conv.name}</span>
                <span className="text-[11px] text-gray-500 shrink-0">
                  {formatTime(conv.last_interaction)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2 mt-0.5">
                <span className="text-xs text-gray-500 truncate">{conv.phone_number}</span>
                <span
                  className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded-full text-white ${badge.color}`}
                >
                  {badge.label}
                </span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
