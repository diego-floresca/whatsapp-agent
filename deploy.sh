#!/bin/bash

IMAGE_TAG="v1"
PROJECT_ID="lunatic-analytics"
REPO="artifact-repository-1"
REGION="northamerica-south1"
SERVICE_NAME="whatsapp-agent"

# URL Imagen
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE_NAME:$IMAGE_TAG"

echo "🚧 1. Construyendo imagen: $IMAGE_TAG..."
gcloud builds submit --tag $IMAGE_URI .

echo "🚀 2. Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated #\
#  --set-env-vars PROJECT_ID="lunatic-analytics" \
#  --set-env-vars BUCKET_NAME="lunatic-whatsapp-audios" \
#  --set-env-vars DATABASE_NAME="agent-whatsapp-chats-database" \
#  --set-env-vars META_ACCESS_TOKEN="EAAUN4khCrRQBQ6lhRF6qNtZCwGxqDJQXaEH0f8ojQCnbmDk9zxby03khI1jl5mlu1fZByJjpvUz7ZANZAIrDb8XeOAYnn53Vzj6iwy0gdVlrQGUYIynSnaJCsfbkQUuxC69jRhWi7QT5P8XcS48ga24vh2ICjeIN10su9YMBzZCUVynvfZAUJwpbS7F6XZAJTXnIwzcKrZCOJuXzBKsgMDBzgZCKWieIUJrVlGgZDZD" \
#  --set-env-vars WEBHOOK_VERIFY_TOKEN="BosEn_tka0_QTFKYr_Pe4w"\
#  --set-env-vars PHONE_NUMBER_ID="959889483881739"

echo "✅ ¡Despliegue completado!"