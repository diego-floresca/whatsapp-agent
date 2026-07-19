import { Router, Request, Response } from 'express';
import {
  getConversations,
  getMessages,
  toggleAI,
  saveHumanMessage,
} from '../services/firestoreService';
import { sendWhatsAppMessage } from '../services/metaService';
import { addClient } from '../sse/sseManager';

const router = Router();

// IMPORTANTE: /stream debe ir ANTES de /:waId para que Express no lo interprete como parámetro
router.get('/stream', (req: Request, res: Response) => {
  addClient(res);
});

router.get('/', async (_req: Request, res: Response) => {
  try {
    const conversations = await getConversations();
    res.json(conversations);
  } catch (err) {
    console.error('Error al obtener conversaciones:', err);
    res.status(500).json({ error: 'Error al obtener conversaciones' });
  }
});

router.get('/:waId/messages', async (req: Request, res: Response) => {
  try {
    const messages = await getMessages(req.params.waId);
    res.json(messages);
  } catch (err) {
    console.error('Error al obtener mensajes:', err);
    res.status(500).json({ error: 'Error al obtener mensajes' });
  }
});

router.post('/:waId/send', async (req: Request, res: Response) => {
  const { waId } = req.params;
  const { content } = req.body as { content?: string };

  if (!content || !content.trim()) {
    res.status(400).json({ error: 'El contenido del mensaje es requerido' });
    return;
  }

  try {
    // Enviar via Meta API
    await sendWhatsAppMessage(waId, content.trim());

    // Guardar en Firestore con role: "human"
    await saveHumanMessage(waId, content.trim());

    res.json({ ok: true });
  } catch (err) {
    console.error('Error al enviar mensaje:', err);
    const message = err instanceof Error ? err.message : 'Error desconocido';
    res.status(500).json({ error: `Error al enviar: ${message}` });
  }
});

router.patch('/:waId/ai-toggle', async (req: Request, res: Response) => {
  const { waId } = req.params;
  const { enabled } = req.body as { enabled?: boolean };

  if (typeof enabled !== 'boolean') {
    res.status(400).json({ error: 'El campo "enabled" (boolean) es requerido' });
    return;
  }

  try {
    await toggleAI(waId, enabled);
    res.json({ ok: true, ai_enabled: enabled });
  } catch (err) {
    console.error('Error al actualizar ai_enabled:', err);
    res.status(500).json({ error: 'Error al actualizar ai_enabled' });
  }
});

export default router;
