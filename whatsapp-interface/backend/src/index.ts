import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { initFirebase } from './services/firebase';
import { initFirestoreListener, initFraudScoresListener } from './sse/sseManager';
import conversationsRouter from './routes/conversations';
import webhookRouter from './routes/webhook';

// Inicializar Firebase antes de cualquier otra cosa
initFirebase();

const app = express();
const PORT = process.env.PORT ?? 3001;

app.use(
  cors({
    origin: ['http://localhost:5174', 'http://localhost:4173'],
    credentials: true,
  })
);
app.use(express.json());

app.use('/api/conversations', conversationsRouter);
app.use('/webhook', webhookRouter);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`🚀 Backend corriendo en http://localhost:${PORT}`);
  // Iniciar listener de Firestore para SSE (después de que Express esté listo)
  initFirestoreListener();
  initFraudScoresListener();
});
