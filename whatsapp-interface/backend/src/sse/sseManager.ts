import { Response } from 'express';
import { subscribeToUsers, subscribeToFraudScores } from '../services/firestoreService';

const clients = new Set<Response>();
let unsubscribeUsers: (() => void) | null = null;
let unsubscribeFraud: (() => void) | null = null;

export function addClient(res: Response): void {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // nginx compatibility
  res.flushHeaders();

  // Heartbeat cada 30s para mantener la conexión viva
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\n\n');
  }, 30_000);

  clients.add(res);

  res.on('close', () => {
    clearInterval(heartbeat);
    clients.delete(res);
  });
}

export function broadcast(event: string, data: unknown): void {
  const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const client of clients) {
    client.write(payload);
  }
}

export function initFirestoreListener(): void {
  if (unsubscribeUsers) return; // Ya inicializado

  unsubscribeUsers = subscribeToUsers(() => {
    broadcast('update', { type: 'conversations' });
  });

  console.log('✅ Listener Firestore SSE activo (conversaciones)');
}

export function initFraudScoresListener(): void {
  if (unsubscribeFraud) return; // Ya inicializado

  unsubscribeFraud = subscribeToFraudScores((waId, score) => {
    broadcast('fraud_update', score);
  });

  console.log('✅ Listener Firestore SSE activo (fraud_scores)');
}
