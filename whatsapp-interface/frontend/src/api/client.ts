import type { Conversation, Message } from '../types';

const BASE = '/api/conversations';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { error?: string };
    throw new Error(body.error ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchConversations(): Promise<Conversation[]> {
  return request<Conversation[]>('/');
}

export async function fetchMessages(waId: string): Promise<Message[]> {
  return request<Message[]>(`/${waId}/messages`);
}

export async function sendMessage(waId: string, content: string): Promise<void> {
  await request<void>(`/${waId}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
}

export async function toggleAI(waId: string, enabled: boolean): Promise<void> {
  await request<void>(`/${waId}/ai-toggle`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
}

export function createSSEConnection(onUpdate: () => void): EventSource {
  const es = new EventSource(`${BASE}/stream`);
  es.addEventListener('update', onUpdate);
  es.onerror = () => {
    // Reconexión automática — EventSource lo maneja por sí solo
    console.warn('SSE: conexión interrumpida, reconectando...');
  };
  return es;
}
