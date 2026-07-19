export interface Conversation {
  waId: string;
  name: string;
  phone_number: string;
  ai_enabled: boolean;
  status: 'en_curso' | 'resuelto' | 'sin_resolver' | string;
  last_interaction: string | null;
}

export interface Message {
  id: string;
  role: 'user' | 'ai' | 'human';
  content: string;
  type: string;
  timestamp: string | null;
}
