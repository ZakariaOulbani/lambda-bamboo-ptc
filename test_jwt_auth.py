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
        print("[INFO] Appel a l'API OAuth2 ENGIE...")
        print(f"   Client ID: {os.getenv('ENGIE_CLIENT_ID', 'NON CONFIGURE')}")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'dev')}")
        print()

        token = get_jwt_token()

        print("[OK] Token JWT obtenu avec succes!")
        print(f"   Token: {token[:50]}..." if len(token) > 50 else f"   Token: {token}")
        print()
        return token

    except AuthenticationError as e:
        print(f"[ERREUR] Erreur d'authentification: {e}")
        print()
        print("[ATTENTION] Verifiez que les variables d'environnement sont configurees:")
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
        print("[SKIP] Test ignore (pas de token disponible)")
        print()
        return

    # Creer un event simule avec le token
    event = {
        'headers': {
            'Authorization': f'Bearer {token}'
        }
    }

    try:
        print("[INFO] Validation du token...")
        result = validate_jwt_token(event)

        print("[OK] Token valide avec succes!")
        print(f"   Valid: {result['valid']}")
        print(f"   Validated at: {result['validated_at']}")
        print()

    except TokenValidationError as e:
        print(f"[ERREUR] Erreur de validation: {e}")
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
        print("[INFO] Validation d'un token invalide...")
        validate_jwt_token(event)
        print("[ERREUR] Le token aurait du etre rejete!")
        print()

    except TokenValidationError as e:
        print(f"[OK] Token invalide correctement rejete")
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
        print("[INFO] Validation sans token...")
        validate_jwt_token(event)
        print("[ERREUR] L'absence de token aurait du etre detectee!")
        print()

    except TokenValidationError as e:
        print(f"[OK] Absence de token correctement detectee")
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
        print(f"[OK] Token obtenu: {token[:30]}...")

        # Creer un event complet
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

        print("[INFO] Appel du handler Lambda avec authentification...")
        response = lambda_handler(event, None)

        print(f"[OK] Reponse recue: {response['statusCode']}")

        if response['statusCode'] == 200:
            print("[OK] Authentification JWT fonctionne correctement!")
        else:
            print(f"[ATTENTION] Code de reponse inattendu: {response['statusCode']}")
            print(f"   Body: {response['body'][:200]}...")

        print()

    except Exception as e:
        print(f"[ERREUR] Erreur lors du test d'integration: {e}")
        print()


def main():
    """Fonction principale"""
    print("\n")
    print("TEST D'AUTHENTIFICATION JWT - BAMBOO-PTC")
    print("=" * 70)
    print()

    # Verifier la configuration
    client_id = os.getenv('ENGIE_CLIENT_ID')
    client_secret = os.getenv('ENGIE_CLIENT_SECRET')

    if not client_id or not client_secret or client_id == 'your_client_id_here':
        print("[ATTENTION] Les credentials ENGIE ne sont pas configures!")
        print()
        print("Pour tester avec de vrais credentials:")
        print("1. Ouvrez le fichier .env")
        print("2. Remplacez les valeurs suivantes:")
        print("   ENGIE_CLIENT_ID=votre_vrai_client_id")
        print("   ENGIE_CLIENT_SECRET=votre_vrai_client_secret")
        print()
        print("Les tests vont s'executer mais echoueront a l'obtention du token.")
        print()
        input("Appuyez sur Entree pour continuer...")
        print()

    # Executer les tests
    token = test_get_token()
    test_validate_token(token)
    test_invalid_token()
    test_missing_token()

    # Test d'integration si on a un token
    if token:
        test_full_integration()

    # Resume
    print("=" * 70)
    print("[OK] TESTS TERMINES")
    print("=" * 70)
    print()
    print("Prochaines etapes:")
    print("   1. Configurez les vrais credentials ENGIE dans .env")
    print("   2. Testez avec: python3 test_jwt_auth.py")
    print("   3. Deployez avec: ./deploy-local.sh")
    print()


if __name__ == '__main__':
    main()
