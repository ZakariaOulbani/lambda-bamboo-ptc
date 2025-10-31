#!/bin/bash
# Script de deploiement pour AWS Lambda
# Cree un package propre sans dependances de test

set -e  # Arret en cas d'erreur

echo "======================================"
echo "Creation du package Lambda..."
echo "======================================"

# Nom du fichier ZIP
DEPLOYMENT_ZIP="lambda-deployment-clean.zip"

# Nettoyer les anciens builds
echo "Nettoyage des anciens fichiers..."
rm -rf package/
rm -f $DEPLOYMENT_ZIP

# Creer le dossier de build
mkdir -p package

# Installer les dependances de PRODUCTION uniquement
echo "Installation des dependances de production..."
pip install -r requirements-prod.txt -t package/ --upgrade

# Copier le code source
echo "Copie du code source..."
cp -r src package/

# Creer le ZIP (SANS les fichiers de test)
echo "Creation du fichier ZIP..."
cd package
zip -r ../$DEPLOYMENT_ZIP . -x "*.pyc" "*__pycache__*" "*.git*" "*test*" "*pytest*"
cd ..

# Afficher les informations
echo ""
echo "======================================"
echo "Package cree avec succes!"
echo "======================================"
echo "Fichier: $DEPLOYMENT_ZIP"
echo "Taille: $(du -h $DEPLOYMENT_ZIP | cut -f1)"
echo ""
echo "Verification du contenu..."
unzip -l $DEPLOYMENT_ZIP | grep -E "(src/|pydantic|requests|dotenv)" | head -20
echo "..."
echo ""
echo "======================================"
echo "Pret pour upload sur AWS Lambda"
echo "======================================"
echo ""
echo "IMPORTANT - Configuration AWS Lambda:"
echo ""
echo "1. Upload du fichier: $DEPLOYMENT_ZIP"
echo ""
echo "2. Variables d'environnement a configurer:"
echo "   - JWT_AUTHENTICATION_ENABLED = 'true' ou 'false'"
echo "   - ENGIE_CLIENT_ID = (si JWT active)"
echo "   - ENGIE_CLIENT_SECRET = (si JWT active)"
echo "   - ENVIRONMENT = 'dev' ou 'prod'"
echo "   - THINGWORX_BASE_URL = (URL ThingWorx)"
echo "   - THINGWORX_APP_KEY = (App Key)"
echo ""
echo "3. Handler: src.handler.lambda_handler"
echo ""
echo "4. Runtime: Python 3.12"
echo ""
echo "5. Timeout recommande: 30 secondes"
echo ""
echo "6. Memoire recommandee: 512 MB"
echo ""
