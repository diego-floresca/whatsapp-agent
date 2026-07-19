import { useState, useCallback } from 'react';
import { ConversationList } from './components/ConversationList';
import { ChatHeader } from './components/ChatHeader';
import { ChatWindow } from './components/ChatWindow';
import { useConversations } from './hooks/useConversations';
import { useMessages } from './hooks/useMessages';

export default function App() {
  const [activeWaId, setActiveWaId] = useState<string | null>(null);
  const { conversations, loading: convsLoading, refresh: refreshConvs } = useConversations();
  const { messages, loading: msgsLoading, sending, error, sendMessage } = useMessages(activeWaId);

  const activeConversation = conversations.find((c) => c.waId === activeWaId) ?? null;

  // Cuando el toggle de IA cambia, actualizamos la lista de conversaciones
  const handleAIToggled = useCallback(
    (_enabled: boolean) => {
      refreshConvs();
    },
    [refreshConvs]
  );

  return (
    <div className="flex h-screen bg-[#0a0a0a] overflow-hidden">
      {/* Panel izquierdo: lista de conversaciones */}
      <aside className="w-80 shrink-0 flex flex-col border-r border-[#1e1e1e] bg-[#141414]">
        {/* Header del panel */}
        <div className="px-4 py-4 border-b border-[#1e1e1e] shrink-0">
          <h1 className="text-sm font-semibold text-gray-100">Support Dashboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {conversations.length} conversación{conversations.length !== 1 ? 'es' : ''}
          </p>
        </div>

        {/* Lista */}
        <div className="flex-1 overflow-y-auto">
          <ConversationList
            conversations={conversations}
            loading={convsLoading}
            activeWaId={activeWaId}
            onSelect={setActiveWaId}
          />
        </div>
      </aside>

      {/* Panel derecho: chat */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#0a0a0a]">
        {activeConversation ? (
          <>
            <ChatHeader
              conversation={activeConversation}
              onAIToggled={handleAIToggled}
            />
            <ChatWindow
              messages={messages}
              loading={msgsLoading}
              sending={sending}
              error={error}
              aiEnabled={activeConversation.ai_enabled}
              onSend={sendMessage}
            />
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
            <div className="w-12 h-12 rounded-xl bg-[#1e1e1e] flex items-center justify-center text-2xl">
              💬
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">Selecciona una conversación</p>
              <p className="text-xs text-gray-600 mt-1">
                Elige una conversación del panel izquierdo para ver el historial
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
