import { FieldValue, Timestamp } from 'firebase-admin/firestore';
import { getDb } from './firebase';

export interface Conversation {
  waId: string;
  name: string;
  phone_number: string;
  ai_enabled: boolean;
  status: string;
  last_interaction: string | null;
}

export interface Message {
  id: string;
  role: 'user' | 'ai' | 'human';
  content: string;
  type: string;
  timestamp: string | null;
}

function toISO(ts: unknown): string | null {
  if (!ts) return null;
  if (ts instanceof Timestamp) return ts.toDate().toISOString();
  if (ts instanceof Date) return ts.toISOString();
  // Firestore raw object { _seconds, _nanoseconds }
  if (typeof ts === 'object' && ts !== null && '_seconds' in ts) {
    return new Date((ts as { _seconds: number })._seconds * 1000).toISOString();
  }
  return null;
}

export async function getConversations(): Promise<Conversation[]> {
  const db = getDb();
  const snapshot = await db
    .collection('users')
    .orderBy('last_interaction', 'desc')
    .get();

  return snapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      waId: doc.id,
      name: data.name ?? 'Desconocido',
      phone_number: data.phone_number ?? doc.id,
      ai_enabled: data.ai_enabled !== false, // default true
      status: data.status ?? 'en_curso',
      last_interaction: toISO(data.last_interaction),
    };
  });
}

export async function getMessages(waId: string): Promise<Message[]> {
  const db = getDb();
  const snapshot = await db
    .collection('users')
    .doc(waId)
    .collection('messages')
    .orderBy('timestamp', 'asc')
    .get();

  return snapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      id: doc.id,
      role: data.role as 'user' | 'ai' | 'human',
      content: data.content ?? '',
      type: data.type ?? 'text',
      timestamp: toISO(data.timestamp),
    };
  });
}

export async function toggleAI(waId: string, enabled: boolean): Promise<void> {
  const db = getDb();
  await db.collection('users').doc(waId).update({ ai_enabled: enabled });
}

export async function saveHumanMessage(waId: string, content: string): Promise<void> {
  const db = getDb();
  await db
    .collection('users')
    .doc(waId)
    .collection('messages')
    .add({
      role: 'human',
      content,
      type: 'text',
      timestamp: FieldValue.serverTimestamp(),
    });

  // También actualizamos last_interaction del usuario
  await db.collection('users').doc(waId).update({
    last_interaction: FieldValue.serverTimestamp(),
  });
}

export function subscribeToUsers(callback: () => void): () => void {
  const db = getDb();
  const unsubscribe = db.collection('users').onSnapshot(() => {
    callback();
  });
  return unsubscribe;
}

// ── Fraud scores ──────────────────────────────────────────────────────────────

export interface FraudScore {
  waId: string;
  score: number;
  max_score: number;        // pico histórico — nunca baja aunque la conversación se resuelva
  risk_level: 'bajo' | 'medio' | 'alto';
  scam_type: string | null;
  evidence: string | null;
  reasoning: string | null;
  updated_at: string | null;
  alerted: boolean;
}

export async function getFraudScores(): Promise<FraudScore[]> {
  const db = getDb();
  const snapshot = await db.collection('fraud_scores').get();
  return snapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      waId: doc.id,
      score: data.score ?? 0,
      max_score: data.max_score ?? data.score ?? 0,
      risk_level: data.risk_level ?? 'bajo',
      scam_type: data.scam_type ?? null,
      evidence: data.evidence ?? null,
      reasoning: data.reasoning ?? null,
      updated_at: toISO(data.updated_at),
      alerted: data.alerted ?? false,
    };
  });
}

export function subscribeToFraudScores(
  callback: (waId: string, score: FraudScore) => void
): () => void {
  const db = getDb();
  const unsubscribe = db.collection('fraud_scores').onSnapshot((snapshot) => {
    snapshot.docChanges().forEach((change) => {
      if (change.type === 'added' || change.type === 'modified') {
        const data = change.doc.data();
        callback(change.doc.id, {
          waId: change.doc.id,
          score: data.score ?? 0,
          max_score: data.max_score ?? data.score ?? 0,
          risk_level: data.risk_level ?? 'bajo',
          scam_type: data.scam_type ?? null,
          evidence: data.evidence ?? null,
          reasoning: data.reasoning ?? null,
          updated_at: toISO(data.updated_at),
          alerted: data.alerted ?? false,
        });
      }
    });
  });
  return unsubscribe;
}
