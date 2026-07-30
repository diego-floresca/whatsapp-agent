import { useEffect, useState, useCallback, useRef } from 'react';
import { fetchMessages, sendMessage as apiSendMessage, createSSEConnection } from '../api/client';
import type { Message } from '../types';

export function useMessages(waId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const prevWaId = useRef<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const refresh = useCallback(async (id: string) => {
    try {
      const data = await fetchMessages(id);
      setMessages(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando mensajes');
    }
  }, []);

  // Carga inicial y recarga cuando cambia la conversación activa
  useEffect(() => {
    if (!waId) {
      setMessages([]);
      return;
    }

    if (waId !== prevWaId.current) {
      setLoading(true);
      prevWaId.current = waId;
    }

    refresh(waId).finally(() => setLoading(false));
  }, [waId, refresh]);

  // SSE: refresca mensajes cuando llegan nuevos (evento 'update' del backend)
  useEffect(() => {
    if (!waId) return;

    const es = createSSEConnection(() => {
      refresh(waId);
    });
    esRef.current = es;

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [waId, refresh]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!waId) return;
      setSending(true);
      setError(null);
      try {
        await apiSendMessage(waId, content);
        await refresh(waId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al enviar');
        throw err;
      } finally {
        setSending(false);
      }
    },
    [waId, refresh]
  );

  return { messages, loading, sending, error, sendMessage, refresh: () => waId && refresh(waId) };
}
