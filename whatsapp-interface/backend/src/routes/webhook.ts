import { Router, Request, Response } from 'express';
import { getDb } from '../services/firebase';
import { FieldValue } from 'firebase-admin/firestore';

const router = Router();

const VERIFY_TOKEN = process.env.WEBHOOK_VERIFY_TOKEN ?? '';

// Verificación del webhook (Meta lo llama al configurar)
router.get('/', (req: Request, res: Response) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  if (mode === 'subscribe' && token === VERIFY_TOKEN) {
    console.log('✅ Webhook verificado');
    res.status(200).send(challenge);
  } else {
    res.status(403).send('Forbidden');
  }
});

// Recepción de mensajes de WhatsApp
router.post('/', async (req: Request, res: Response) => {
  // Meta espera 200 inmediato
  res.sendStatus(200);

  try {
    const entry = req.body?.entry?.[0];
    const changes = entry?.changes?.[0];
    const value = changes?.value;

    if (!value?.messages) return;

    const message = value.messages[0];
    const contact = value.contacts?.[0];

    const waId: string = contact?.wa_id;
    const name: string = contact?.profile?.name ?? 'Desconocido';
    const msgType: string = message.type;

    if (!waId) return;

    const db = getDb();
    const userRef = db.collection('users').doc(waId);

    // Guardar mensaje primero — el listener de SSE dispara al actualizar
    // last_interaction, así que el mensaje ya debe existir antes de ese update.
    let content = '';
    if (msgType === 'text') {
      content = message.text?.body ?? '';
    } else if (msgType === 'audio') {
      content = `[AUDIO: ${message.audio?.id}]`;
    } else if (msgType === 'image') {
      content = `[IMAGEN: ${message.image?.id}]`;
    } else {
      content = `[${msgType.toUpperCase()}]`;
    }

    await userRef.collection('messages').add({
      role: 'user',
      content,
      type: msgType,
      timestamp: FieldValue.serverTimestamp(),
    });

    // Crear o actualizar usuario — este write dispara el SSE al frontend
    const userSnap = await userRef.get();
    if (!userSnap.exists) {
      await userRef.set({
        name,
        phone_number: waId,
        ai_enabled: false,
        status: 'en_curso',
        created_at: FieldValue.serverTimestamp(),
        last_interaction: FieldValue.serverTimestamp(),
      });
    } else {
      await userRef.update({ last_interaction: FieldValue.serverTimestamp() });
    }

    console.log(`📩 Mensaje de ${name} (${waId}): ${content.slice(0, 60)}`);
  } catch (err) {
    console.error('❌ Error procesando webhook:', err);
  }
});

export default router;
