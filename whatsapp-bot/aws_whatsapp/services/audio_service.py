import requests
import logging
import os
import boto3

logger = logging.getLogger(__name__)

# CONFIGURACIÓN
META_VERSION = "v25.0"
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
BUCKET_NAME = os.environ.get("BUCKET_NAME") 
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Cliente de S3
try:
    s3_client = boto3.client('s3', region_name=REGION)
except Exception as e:
    logger.error(f"❌ Error inicializando S3 client: {e}")

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
        return response.content, response.headers.get("Content-Type")
    except Exception as e:
        logger.error(f"❌ Error descargando bytes: {e}")
        return None, None

def upload_to_s3(file_bytes, file_name, content_type):
    """
    Sube el archivo a Amazon S3 y retorna la URI interna (s3://)
    """
    try:
        if not BUCKET_NAME:
            logger.error("❌ BUCKET_NAME no está configurado.")
            return None
            
        object_key = f"audios/{file_name}"
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type
        )
        
        logger.info(f"☁️ Archivo subido a S3: {object_key}")
        
        return f"s3://{BUCKET_NAME}/{object_key}"
    except Exception as e:
        logger.error(f"❌ Error subiendo a S3: {e}")
        return None