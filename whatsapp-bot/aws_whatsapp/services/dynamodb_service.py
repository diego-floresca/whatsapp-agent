import os
import time
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

# --- CONFIGURATION ---
REGION = os.environ.get("AWS_REGION", "us-east-1")
USERS_TABLE_NAME = os.environ.get("DYNAMODB_USERS_TABLE", "whatsapp_users")
MESSAGES_TABLE_NAME = os.environ.get("DYNAMODB_MESSAGES_TABLE", "whatsapp_messages")

# Initialize DynamoDB resource
try:
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    users_table = dynamodb.Table(USERS_TABLE_NAME)
    messages_table = dynamodb.Table(MESSAGES_TABLE_NAME)
    print(f"✅ DynamoDB client connected to tables: {USERS_TABLE_NAME}, {MESSAGES_TABLE_NAME}")
except Exception as e:
    print(f"❌ Error initializing DynamoDB client: {e}")
    # En un entorno serverless esto fallará si no hay credenciales
    pass

def get_or_create_user(phone_number: str, name: str = "Unknown"):
    """
    Verifica si el usuario existe. Si no, lo crea.
    Actualiza la última interacción.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        response = users_table.get_item(Key={'phone_number': phone_number})
        if 'Item' in response:
            # User exists, update last interaction
            users_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression="set last_interaction = :t",
                ExpressionAttributeValues={':t': now_iso}
            )
        else:
            # Create new user
            users_table.put_item(
                Item={
                    'phone_number': phone_number,
                    'name': name,
                    'created_at': now_iso,
                    'last_interaction': now_iso,
                    'status': 'active'
                }
            )
    except Exception as e:
        print(f"Error accediendo a DynamoDB Users Table: {e}")

def add_message(phone_number: str, role: str, content: str, msg_type: str = "text"):
    """
    Guarda un mensaje en la tabla de mensajes.
    role: 'user' (lo que escribe el cliente) o 'ai' (lo que respondemos)
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    # Usamos timestamp + un id corto para evitar colisiones en la sort key
    sort_key = f"{now_iso}_{uuid.uuid4().hex[:6]}"
    
    try:
        messages_table.put_item(
            Item={
                'phone_number': phone_number,  # Partition Key
                'timestamp_id': sort_key,      # Sort Key
                'role': role,
                'content': content,
                'type': msg_type,
                'timestamp': now_iso
            }
        )
    except Exception as e:
        print(f"Error accediendo a DynamoDB Messages Table: {e}")

def get_chat_history(phone_number: str, limit: int = 10):
    """
    Recupera los últimos X mensajes para dárselos de contexto a la IA.
    Retorna una lista de diccionarios ordenada cronológicamente.
    """
    try:
        # Query messages for the user, ordered by timestamp (descending) to get the latest `limit` messages
        response = messages_table.query(
            KeyConditionExpression=Key('phone_number').eq(phone_number),
            ScanIndexForward=False, # Descending order
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        history = []
        for item in items:
            history.append({
                "role": item.get("role"),
                "content": item.get("content")
            })
            
        # Invertimos para que el mensaje más viejo esté al inicio (orden de lectura)
        return history[::-1]
    except Exception as e:
        print(f"Error accediendo a DynamoDB Messages Table: {e}")
        return []
