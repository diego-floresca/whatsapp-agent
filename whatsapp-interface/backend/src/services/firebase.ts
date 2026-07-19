import admin from 'firebase-admin';
import { getFirestore, Firestore } from 'firebase-admin/firestore';

let db: Firestore;

export function initFirebase(): Firestore {
  if (db) return db;

  if (!admin.apps.length) {
    admin.initializeApp({
      credential: admin.credential.applicationDefault(),
    });
  }

  const databaseId = process.env.DATABASE_NAME || '(default)';
  db = getFirestore(admin.app(), databaseId);

  console.log(`✅ Firebase Admin conectado — database: "${databaseId}"`);
  return db;
}

export function getDb(): Firestore {
  if (!db) throw new Error('Firebase no inicializado. Llama initFirebase() primero.');
  return db;
}
