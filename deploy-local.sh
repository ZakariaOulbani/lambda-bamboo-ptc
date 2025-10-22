#!/bin/bash

set -e

echo "Déploiement sur LocalStack..."

ENDPOINT="http://localstack:4566"
FUNCTION_NAME="bamboo-ptc-connector"

# Exécuter les commandes dans le container dev
docker-compose exec -T dev bash << 'EOF'
set -e

echo "Création du package Lambda..."

# Supprimer l'ancien package s'il existe
rm -rf package lambda-deployment.zip

# Créer un dossier temporaire
mkdir -p package

# Copier notre code dedans
cp -r src package/

# Installer les dépendances Python dans ce dossier
pip install -r requirements.txt -t package/ -q

# Créer un zip avec tout
cd package && zip -r ../lambda-deployment.zip . -q && cd ..

# Nettoyer le dossier temporaire
rm -rf package

echo "Déploiement de la fonction Lambda..."

# Déployer sur LocalStack
aws --endpoint-url=http://localstack:4566 lambda create-function \
  --function-name bamboo-ptc-connector \
  --runtime python3.12 \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler src.handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 30 \
  --memory-size 256 2>/dev/null || \
aws --endpoint-url=http://localstack:4566 lambda update-function-code \
  --function-name bamboo-ptc-connector \
  --zip-file fileb://lambda-deployment.zip > /dev/null

echo "Attente du démarrage de la Lambda..."
aws --endpoint-url=http://localstack:4566 lambda wait function-active-v2 --function-name bamboo-ptc-connector

echo "Configuration de la Lambda Function URL..."
FUNCTION_URL=$(aws --endpoint-url=http://localstack:4566 lambda create-function-url-config \
  --function-name bamboo-ptc-connector \
  --auth-type NONE \
  --query 'FunctionUrl' --output text 2>/dev/null || \
  aws --endpoint-url=http://localstack:4566 lambda get-function-url-config \
  --function-name bamboo-ptc-connector \
  --query 'FunctionUrl' --output text)

echo ""
echo "Déploiement terminé !"
echo ""
echo "Lambda Function URL: $FUNCTION_URL"
echo ""
echo "Pour tester, utilisez:"
echo "  docker-compose exec dev python3 test_lambda.py"
echo ""
EOF
