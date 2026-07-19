import { useEffect, useState, useCallback, useRef } from 'react';
import { fetchMessages, sendMessage as apiSendMessage } from '../api/client';
import type { Message } from '../types';

export function useMessages(waId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const prevWaId = useRef<string | null>(null);

  const refresh = useCallback(async (id: string) => {
    try {
      const data = await fetchMessages(id);
      setMessages(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando mensajes');
    }
  }, []);

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
