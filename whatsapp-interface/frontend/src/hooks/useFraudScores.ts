import { useEffect, useRef, useState } from 'react';
import { createSSEConnection, addFraudListener, fetchFraudScores } from '../api/client';
import type { FraudScore } from '../types';

export function useFraudScores() {
  const [scores, setScores] = useState<Map<string, FraudScore>>(new Map());
  const esRef = useRef<EventSource | null>(null);

  // Carga inicial desde Firestore al montar
  useEffect(() => {
    fetchFraudScores().then((all) => {
      setScores((prev) => {
        const next = new Map(prev);
        for (const s of all) next.set(s.waId, s);
        return next;
      });
    }).catch((err) => console.warn('Error cargando fraud scores iniciales:', err));
  }, []);

  // Actualizaciones en tiempo real vía SSE
  useEffect(() => {
    const es = createSSEConnection(() => {});

    addFraudListener(es, (score) => {
      setScores((prev) => {
        const next = new Map(prev);
        next.set(score.waId, score);
        return next;
      });
    });

    esRef.current = es;

    return () => {
      es.close();
    };
  }, []);

  return scores;
}
