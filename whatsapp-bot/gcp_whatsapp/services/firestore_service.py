import os
import time
from google.cloud import firestore
from google.api_core.exceptions import NotFound

# --- CONFIGURACIÓN ---
PROJECT_ID = os.environ.get("PROJECT_ID")
DATABASE_NAME = os.environ.get("DATABASE_NAME")

# Inicializamos el cliente una sola vez (Singleton pattern implícito)
# Al estar en GCP (Cloud Run), esto toma las credenciales automáticamente.
try:
    db = firestore.Client(project=PROJECT_ID, database=DATABASE_NAME)
    print(f"✅ Cliente Firestore conectado a: {DATABASE_NAME}")
except Exception as e:
    print(f"❌ Error al iniciar cliente Firestore: {e}")
    raise e
    
def get_or_create_user(phone_number: str, name: str = "Unknown"):
    """
    Verifica si el usuario existe. Si no, lo crea.
    Actualiza la última interacción.
    """
    user_ref = db.collection("users").document(phone_number)
    
    try:
        user_doc = user_ref.get()
        if user_doc.exists:
            # Solo actualizamos la última interacción
            user_ref.update({"last_interaction": firestore.SERVER_TIMESTAMP})
        else:
            # Creamos el usuario nuevo
            user_ref.set({
                "name": name,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_interaction": firestore.SERVER_TIMESTAMP,
                "status": "active"
            })
    except Exception as e:
        print(f"Error accediendo a Firestore: {e}")
        # En producción, aquí usaríamos un logger real (como Cloud Logging)

def add_message(phone_number: str, role: str, content: str, msg_type: str = "text"):
    """
    Guarda un mensaje en la subcolección 'messages' del usuario.
    role: 'user' (lo que escribe el cliente) o 'ai' (lo que respondemos)
    """
    # Referencia al documento del usuario
    user_ref = db.collection("users").document(phone_number)
    
    # Referencia a la subcolección de mensajes
    messages_ref = user_ref.collection("messages")
    
    new_message = {
        "role": role, 
        "content": content,
        "type": msg_type,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    
    # Add genera un ID automático para el documento del mensaje
    messages_ref.add(new_message)

def get_chat_history(phone_number: str, limit: int = 10):
    """
    Recupera los últimos X mensajes para dárselos de contexto a la IA.
    Retorna una lista de diccionarios ordenada cronológicamente.
    """
    user_ref = db.collection("users").document(phone_number)
    
    # Query: Ordenar por timestamp descendente (más nuevo primero) para aplicar el límite
    # y luego invertir la lista para que la IA lea en orden cronológico.
    query = user_ref.collection("messages")\
            .order_by("timestamp", direction=firestore.Query.DESCENDING)\
            .limit(limit)
            
    docs = query.stream()
    
    history = []
    for doc in docs:
        msg_data = doc.to_dict()
        # Convertimos el timestamp de Firestore a string o float si es necesario
        # Para simplificar, aquí lo dejamos fuera del payload de texto
        history.append({
            "role": msg_data.get("role"),
            "content": msg_data.get("content")
        })
    
    # Invertimos para que el mensaje más viejo esté al inicio (orden de lectura)
    return history[::-1]