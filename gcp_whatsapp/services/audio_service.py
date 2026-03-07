import requests
import logging
import os
from google.cloud import storage

logger = logging.getLogger(__name__)

# CONFIGURACIÓN
META_VERSION = "v21.0" # Ajusta a v24.0 si confirmaste que esa es la tuya
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
BUCKET_NAME = os.environ.get("BUCKET_NAME") 

# Cliente de Storage (Se autentica solo en Cloud Run)
storage_client = storage.Client()

def get_audio_url(media_id: str):
    """Obtiene la URL temporal de descarga desde Meta."""
    url = f"https://graph.facebook.com/{META_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("url")
    except Exception as e:
        logger.error(f"❌ Error obteniendo URL del audio {media_id}: {e}")
        return None

def download_audio_bytes(media_url: str):
    """Descarga los bytes del audio desde la URL temporal."""
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        # Retorna contenido y el tipo MIME (ej: audio/ogg)
        return response.content, response.headers.get("Content-Type")
    except Exception as e:
        logger.error(f"❌ Error descargando bytes: {e}")
        return None, None

def upload_to_gcs(file_bytes, file_name, content_type):
    """
    Sube el archivo a Google Cloud Storage y retorna la URI interna (gs://)
    """
    try:
        if not BUCKET_NAME:
            logger.error("❌ BUCKET_NAME no está configurado.")
            return None
            
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"audios/{file_name}")
        
        # Subimos el archivo
        blob.upload_from_string(file_bytes, content_type=content_type)
        
        logger.info(f"☁️ Archivo subido a GCS: {blob.name}")
        
        # Retornamos la ruta gs:// para guardarla en Firestore (limpio y seguro)
        return f"gs://{BUCKET_NAME}/{blob.name}"
    except Exception as e:
        logger.error(f"❌ Error subiendo a GCS: {e}")
        return None