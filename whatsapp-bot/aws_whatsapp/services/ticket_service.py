import os
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

REGION = os.environ.get("AWS_REGION", "us-east-1")
TICKETS_TABLE_NAME = os.environ.get("DYNAMODB_TICKETS_TABLE", "whatsapp_tickets")

try:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    tickets_table = dynamodb.Table(TICKETS_TABLE_NAME)
    print(f"✅ DynamoDB tickets table connected: {TICKETS_TABLE_NAME}")
except Exception as e:
    print(f"❌ Error initializing tickets DynamoDB client: {e}")


def crear_ticket(
    order_id: str,
    motivo: str,
    resumen: str,
    prioridad: str,
    phone_number: str,
) -> dict:
    """
    Crea un ticket de escalamiento en DynamoDB.
    Devuelve {"ticket_id": "...", "estado": "abierto"} o {"error": True, "mensaje": "..."}.
    """
    ticket_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        tickets_table.put_item(
            Item={
                "ticket_id": ticket_id,
                "order_id": order_id,
                "motivo": motivo,
                "resumen": resumen,
                "prioridad": prioridad,
                "estado": "abierto",
                "phone_number": phone_number,
                "created_at": now_iso,
            }
        )
        print(f"🎫 Ticket creado: {ticket_id} | orden: {order_id} | motivo: {motivo}")
        return {"ticket_id": ticket_id, "estado": "abierto"}
    except Exception as e:
        print(f"❌ Error creando ticket en DynamoDB: {e}")
        return {"error": True, "mensaje": str(e)}
