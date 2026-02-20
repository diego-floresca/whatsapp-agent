#!/bin/bash

IMAGE_TAG="v5"
PROJECT_ID="lunatic-analytics"
REPO="artifact-repository-1"
REGION="northamerica-south1"
SERVICE_NAME="whatsapp-bot"

# URL Imagen
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE_NAME:$IMAGE_TAG"

echo "🚧 1. Construyendo imagen: $IMAGE_TAG..."
gcloud builds submit --tag $IMAGE_URI .

echo "🚀 2. Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  # actualiza variables
  # --set-env-vars BUCKET_NAME="tu-bucket-real" \
  # --set-env-vars PROJECT_ID=$PROJECT_ID

echo "✅ ¡Despliegue completado!"