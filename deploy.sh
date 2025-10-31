#!/bin/bash
# Script de déploiement pour AWS Lambda
# Crée un package propre sans dépendances de test

set -e  # Arrêt en cas d'erreur

echo "======================================"
echo "🚀 Création du package Lambda..."
echo "======================================"

# Nom du fichier ZIP
DEPLOYMENT_ZIP="lambda-deployment-clean.zip"

# Nettoyer les anciens builds
echo "🧹 Nettoyage des anciens fichiers..."
rm -rf package/
rm -f $DEPLOYMENT_ZIP

# Créer le dossier de build
mkdir -p package

# Installer les dépendances de PRODUCTION uniquement
echo "📦 Installation des dépendances de production..."
pip install -r requirements-prod.txt -t package/ --upgrade

# Copier le code source
echo "📝 Copie du code source..."
cp -r src package/

# Créer le ZIP (SANS les fichiers de test)
echo "🗜️  Création du fichier ZIP..."
cd package
zip -r ../$DEPLOYMENT_ZIP . -x "*.pyc" "*__pycache__*" "*.git*" "*test*" "*pytest*"
cd ..

# Afficher les informations
echo ""
echo "======================================"
echo "✅ Package créé avec succès!"
echo "======================================"
echo "Fichier: $DEPLOYMENT_ZIP"
echo "Taille: $(du -h $DEPLOYMENT_ZIP | cut -f1)"
echo ""
echo "📋 Vérification du contenu..."
unzip -l $DEPLOYMENT_ZIP | grep -E "(src/|pydantic|requests|dotenv)" | head -20
echo "..."
echo ""
echo "======================================"
echo "📤 Prêt pour upload sur AWS Lambda"
echo "======================================"
echo ""
echo "⚠️  IMPORTANT - Configuration AWS Lambda:"
echo ""
echo "1. Upload du fichier: $DEPLOYMENT_ZIP"
echo ""
echo "2. Variables d'environnement à configurer:"
echo "   - JWT_AUTHENTICATION_ENABLED = 'true' ou 'false'"
echo "   - ENGIE_CLIENT_ID = (si JWT activé)"
echo "   - ENGIE_CLIENT_SECRET = (si JWT activé)"
echo "   - ENVIRONMENT = 'dev' ou 'prod'"
echo "   - THINGWORX_BASE_URL = (URL ThingWorx)"
echo "   - THINGWORX_APP_KEY = (App Key)"
echo ""
echo "3. Handler: src.handler.lambda_handler"
echo ""
echo "4. Runtime: Python 3.12"
echo ""
echo "5. Timeout recommandé: 30 secondes"
echo ""
echo "6. Mémoire recommandée: 512 MB"
echo ""
