import { useEffect, useState, useCallback, useRef } from 'react';
import { fetchConversations, createSSEConnection } from '../api/client';
import type { Conversation } from '../types';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchConversations();
      setConversations(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();

    // Conectar SSE para actualizaciones en tiempo real
    const es = createSSEConnection(() => {
      refresh();
    });
    esRef.current = es;

    return () => {
      es.close();
    };
  }, [refresh]);

  return { conversations, loading, error, refresh };
}
