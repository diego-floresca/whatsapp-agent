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

IMAGE_TAG=${IMAGE_TAG:-"v1"}

# Validar variables requeridas de AWS
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$AWS_REGION" ] || [ -z "$ECR_REPO_NAME" ]; then
  echo "❌ Error: AWS_ACCOUNT_ID, AWS_REGION y ECR_REPO_NAME son obligatorios en el .env"
  exit 1
fi

IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG"

echo "🔐 1. Autenticando con AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "🚧 2. Construyendo imagen Docker localmente (para servidores de AWS)..."
docker build --platform linux/amd64 -t $ECR_REPO_NAME:$IMAGE_TAG -f Dockerfile.aws .

echo "🏷️ 3. Etiquetando imagen..."
docker tag $ECR_REPO_NAME:$IMAGE_TAG $IMAGE_URI
docker tag $ECR_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

echo "☁️ 4. Subiendo imagen a AWS ECR..."
docker push $IMAGE_URI
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

echo "🚀 5. Sobre el despliegue a ECS Fargate..."
echo "Nota: AWS App Runner está obsoleto. Ahora debes configurar un Cluster de ECS y un Task Definition en la consola de AWS apuntando a tu nueva imagen en ECR."
echo "Para forzar una actualización manual de tu servicio ECS desde la terminal (una vez creado), puedes usar:"
echo "aws ecs update-service --cluster \$ECS_CLUSTER_NAME --service \$ECS_SERVICE_NAME --force-new-deployment"

echo "✅ ¡Imagen subida exitosamente a AWS!"