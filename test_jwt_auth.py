#!/usr/bin/env python3
"""
Script de test rapide pour l'authentification JWT
Usage: python3 test_jwt_auth.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.auth import get_jwt_token, validate_jwt_token, AuthenticationError, TokenValidationError


def test_get_token():
    """Test 1: Obtenir un token JWT depuis l'API OAuth2 ENGIE"""
    print("=" * 70)
    print("TEST 1: Obtention d'un token JWT")
    print("=" * 70)

    try:
        print("📡 Appel à l'API OAuth2 ENGIE...")
        print(f"   Client ID: {os.getenv('ENGIE_CLIENT_ID', 'NON CONFIGURÉ')}")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'dev')}")
        print()

        token = get_jwt_token()

        print("✅ Token JWT obtenu avec succès!")
        print(f"   Token: {token[:50]}..." if len(token) > 50 else f"   Token: {token}")
        print()
        return token

    except AuthenticationError as e:
        print(f"❌ Erreur d'authentification: {e}")
        print()
        print("⚠️  Vérifiez que les variables d'environnement sont configurées:")
        print("   - ENGIE_CLIENT_ID")
        print("   - ENGIE_CLIENT_SECRET")
        print()
        return None


def test_validate_token(token):
    """Test 2: Valider un token JWT"""
    print("=" * 70)
    print("TEST 2: Validation d'un token JWT")
    print("=" * 70)

    if not token:
        print("⏩ Test ignoré (pas de token disponible)")
        print()
        return

    # Créer un event simulé avec le token
    event = {
        'headers': {
            'Authorization': f'Bearer {token}'
        }
    }

    try:
        print("🔍 Validation du token...")
        result = validate_jwt_token(event)

        print("✅ Token validé avec succès!")
        print(f"   Valid: {result['valid']}")
        print(f"   Validated at: {result['validated_at']}")
        print()

    except TokenValidationError as e:
        print(f"❌ Erreur de validation: {e}")
        print()


def test_invalid_token():
    """Test 3: Tester avec un token invalide"""
    print("=" * 70)
    print("TEST 3: Validation d'un token invalide")
    print("=" * 70)

    event = {
        'headers': {
            'Authorization': 'Bearer invalid_token_12345'
        }
    }

    try:
        print("🔍 Validation d'un token invalide...")
        validate_jwt_token(event)
        print("❌ Le token aurait dû être rejeté!")
        print()

    except TokenValidationError as e:
        print(f"✅ Token invalide correctement rejeté")
        print(f"   Erreur: {e}")
        print()


def test_missing_token():
    """Test 4: Tester sans token"""
    print("=" * 70)
    print("TEST 4: Requête sans token")
    print("=" * 70)

    event = {
        'headers': {}
    }

    try:
        print("🔍 Validation sans token...")
        validate_jwt_token(event)
        print("❌ L'absence de token aurait dû être détectée!")
        print()

    except TokenValidationError as e:
        print(f"✅ Absence de token correctement détectée")
        print(f"   Erreur: {e}")
        print()


def test_full_integration():
    """Test 5: Test d'intégration complet avec le handler"""
    print("=" * 70)
    print("TEST 5: Intégration complète avec le handler Lambda")
    print("=" * 70)

    try:
        # Obtenir un vrai token
        token = get_jwt_token()
        print(f"✅ Token obtenu: {token[:30]}...")

        # Créer un event complet
        event = {
            'httpMethod': 'GET',
            'path': '/locations',
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'queryStringParameters': None,
            'pathParameters': None,
            'body': None
        }

        # Importer et appeler le handler
        from src.handler import lambda_handler

        print("📡 Appel du handler Lambda avec authentification...")
        response = lambda_handler(event, None)

        print(f"✅ Réponse reçue: {response['statusCode']}")

        if response['statusCode'] == 200:
            print("✅ Authentification JWT fonctionne correctement!")
        else:
            print(f"⚠️  Code de réponse inattendu: {response['statusCode']}")
            print(f"   Body: {response['body'][:200]}...")

        print()

    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        print()


def main():
    """Fonction principale"""
    print("\n")
    print("🔐 TEST D'AUTHENTIFICATION JWT - BAMBOO-PTC")
    print("=" * 70)
    print()

    # Vérifier la configuration
    client_id = os.getenv('ENGIE_CLIENT_ID')
    client_secret = os.getenv('ENGIE_CLIENT_SECRET')

    if not client_id or not client_secret or client_id == 'your_client_id_here':
        print("⚠️  ATTENTION: Les credentials ENGIE ne sont pas configurés!")
        print()
        print("Pour tester avec de vrais credentials:")
        print("1. Ouvrez le fichier .env")
        print("2. Remplacez les valeurs suivantes:")
        print("   ENGIE_CLIENT_ID=votre_vrai_client_id")
        print("   ENGIE_CLIENT_SECRET=votre_vrai_client_secret")
        print()
        print("Les tests vont s'exécuter mais échoueront à l'obtention du token.")
        print()
        input("Appuyez sur Entrée pour continuer...")
        print()

    # Exécuter les tests
    token = test_get_token()
    test_validate_token(token)
    test_invalid_token()
    test_missing_token()

    # Test d'intégration si on a un token
    if token:
        test_full_integration()

    # Résumé
    print("=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)
    print()
    print("📋 Prochaines étapes:")
    print("   1. Configurez les vrais credentials ENGIE dans .env")
    print("   2. Testez avec: python3 test_jwt_auth.py")
    print("   3. Déployez avec: ./deploy-local.sh")
    print()


if __name__ == '__main__':
    main()
