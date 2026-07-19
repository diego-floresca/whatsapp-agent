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
