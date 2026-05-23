import requests
import logging
import os
from google.cloud import storage

logger = logging.getLogger(__name__)

# CONFIGURACIÓN
META_VERSION = "v25.0" # Match with messenger_service
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
BUCKET_NAME = os.environ.get("BUCKET_NAME") 

# Cliente de Storage (Se autentica solo en Cloud Run)
storage_client = storage.Client()

def get_image_url(media_id: str):
    """Obtiene la URL temporal de descarga desde Meta."""
    url = f"https://graph.facebook.com/{META_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("url")
    except Exception as e:
        logger.error(f"❌ Error obteniendo URL de la imagen {media_id}: {e}")
        return None

def download_image_bytes(media_url: str):
    """Descarga los bytes de la imagen desde la URL temporal."""
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        # Retorna contenido y el tipo MIME (ej: image/jpeg)
        return response.content, response.headers.get("Content-Type")
    except Exception as e:
        logger.error(f"❌ Error descargando bytes de imagen: {e}")
        return None, None

def upload_image_to_gcs(file_bytes, file_name, content_type):
    """
    Sube el archivo a Google Cloud Storage y retorna la URI interna (gs://)
    """
    try:
        if not BUCKET_NAME:
            logger.error("❌ BUCKET_NAME no está configurado.")
            return None
            
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"images/{file_name}")
        
        # Subimos el archivo
        blob.upload_from_string(file_bytes, content_type=content_type)
        
        logger.info(f"☁️ Imagen subida a GCS: {blob.name}")
        
        # Retornamos la ruta gs:// para guardarla en Firestore
        return f"gs://{BUCKET_NAME}/{blob.name}"
    except Exception as e:
        logger.error(f"❌ Error subiendo imagen a GCS: {e}")
        return None
