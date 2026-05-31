#!/bin/bash

if [ -f .env ]; then
  set -a
  source .env
  set +a
  echo "✅ Archivo .env cargado correctamente."
else
  echo "❌ Error: No se encontró el archivo .env"
  exit 1
fi

# URL Imagen
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE_NAME:$IMAGE_TAG"

echo "🚧 1. Construyendo imagen: $IMAGE_TAG..."
gcloud builds submit --config /dev/stdin . <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.gcp', '-t', '$IMAGE_URI', '.']
images: ['$IMAGE_URI']
EOF

echo "🚀 2. Desplegando a Cloud Run..."

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --update-env-vars "META_ACCESS_TOKEN=${META_ACCESS_TOKEN},PHONE_NUMBER_ID=${PHONE_NUMBER_ID},WEBHOOK_VERIFY_TOKEN=${WEBHOOK_VERIFY_TOKEN},BUCKET_NAME=${BUCKET_NAME},N8N_WEBHOOK_URL=${N8N_WEBHOOK_URL}"

echo "✅ ¡Despliegue completado!"