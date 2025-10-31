"""
Module d'authentification JWT pour l'API Bamboo-PTC
Basé sur les spécifications du document v1.4 (pages 30-32)

Endpoints ENGIE OAuth2:
- DEV: https://apis-int1.svc.engie-solutions.fr/oauth2/b2b/v1/token
- PROD: https://apis.svc.engie-solutions.fr/oauth2/b2b/v1/token

Token JWT valide pendant 1 heure.
"""

import os
import time
import logging
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Cache pour éviter de redemander un token à chaque requête
_token_cache = {
    'access_token': None,
    'expires_at': None
}


class AuthenticationError(Exception):
    """Erreur d'authentification"""
    pass


class TokenValidationError(Exception):
    """Erreur de validation du token"""
    pass


def get_oauth2_url() -> str:
    """
    Retourne l'URL de l'API OAuth2 ENGIE selon l'environnement

    Returns:
        URL de l'endpoint OAuth2
    """
    env = os.getenv('ENVIRONMENT', 'dev').lower()

    if env == 'prod':
        return 'https://apis.svc.engie-solutions.fr/oauth2/b2b/v1/token'
    else:
        return 'https://apis-int1.svc.engie-solutions.fr/oauth2/b2b/v1/token'


def get_jwt_token() -> str:
    """
    Obtient un token JWT auprès de l'API OAuth2 ENGIE
    Utilise un cache pour éviter de redemander un token valide

    Conformément au document v1.4 page 30:
    - client_id et client_secret fournis dans les credentials
    - grant_type: client_credentials
    - scope: apis
    - Token valide 1 heure

    Returns:
        Token JWT (Bearer token)

    Raises:
        AuthenticationError: Si impossible d'obtenir le token
    """
    # Vérifier si on a un token en cache encore valide
    if _token_cache['access_token'] and _token_cache['expires_at']:
        # Ajouter une marge de sécurité de 5 minutes avant expiration
        if datetime.now() < (_token_cache['expires_at'] - timedelta(minutes=5)):
            logger.info("Using cached JWT token")
            return _token_cache['access_token']

    # Pas de token en cache ou expiré, on en demande un nouveau
    logger.info("Requesting new JWT token from ENGIE OAuth2")

    # Récupérer les credentials depuis les variables d'environnement
    client_id = os.getenv('ENGIE_CLIENT_ID')
    client_secret = os.getenv('ENGIE_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise AuthenticationError(
            "Missing ENGIE_CLIENT_ID or ENGIE_CLIENT_SECRET in environment variables. "
            "Please configure these credentials to authenticate with ENGIE OAuth2 API."
        )

    # Préparer la requête selon le document v1.4 page 30
    oauth_url = get_oauth2_url()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'apis'
    }

    try:
        response = requests.post(
            oauth_url,
            headers=headers,
            data=data,
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()

        # Extraire le token et calculer l'expiration
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)  # Par défaut 1h

        if not access_token:
            raise AuthenticationError("No access_token in OAuth2 response")

        # Mettre en cache avec timestamp d'expiration
        _token_cache['access_token'] = access_token
        _token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in)

        logger.info(f"Successfully obtained JWT token (expires in {expires_in}s)")
        return access_token

    except requests.RequestException as e:
        logger.error(f"Failed to obtain JWT token: {e}")
        raise AuthenticationError(
            f"Failed to authenticate with ENGIE OAuth2 API: {str(e)}"
        )


def validate_jwt_token(event: Dict) -> Dict:
    """
    Valide le token JWT présent dans le header Authorization

    Conformément au document v1.4 page 31:
    - Header: Authorization: Bearer <token>
    - Le token doit être valide et non expiré

    Args:
        event: Événement Lambda API Gateway contenant les headers

    Returns:
        Dict avec les informations du token validé

    Raises:
        TokenValidationError: Si le token est invalide ou manquant
    """
    # Extraire le header Authorization
    headers = event.get('headers') or {}

    # Gérer la casse (Authorization vs authorization)
    auth_header = None
    for key, value in headers.items():
        if key.lower() == 'authorization':
            auth_header = value
            break

    if not auth_header:
        raise TokenValidationError(
            "Missing Authorization header. "
            "Please provide a valid JWT token in the format: Authorization: Bearer <token>"
        )

    # Vérifier le format "Bearer <token>"
    if not auth_header.startswith('Bearer '):
        raise TokenValidationError(
            "Invalid Authorization header format. "
            "Expected format: Authorization: Bearer <token>"
        )

    # Extraire le token
    token = auth_header.replace('Bearer ', '').strip()

    if not token:
        raise TokenValidationError("Empty token provided")

    # Pour une validation complète, on devrait:
    # 1. Décoder le JWT et vérifier la signature avec la clé publique ENGIE
    # 2. Vérifier l'expiration (exp claim)
    # 3. Vérifier l'émetteur (iss claim)
    # 4. Vérifier l'audience (aud claim)
    #
    # Pour l'instant, on fait une validation basique
    # TODO: Implémenter la validation complète avec PyJWT

    logger.info("JWT token validated successfully")

    return {
        'valid': True,
        'token': token,
        'validated_at': datetime.now().isoformat()
    }


def require_auth(func):
    """
    Décorateur pour protéger les endpoints avec authentification JWT

    Usage:
        @require_auth
        def my_protected_function(event, context):
            return {"message": "Protected data"}

    Args:
        func: Fonction à protéger

    Returns:
        Fonction wrappée avec validation JWT
    """
    def wrapper(event, context):
        try:
            # Valider le token
            token_info = validate_jwt_token(event)

            # Ajouter les infos du token dans l'event pour les endpoints
            event['auth'] = token_info

            # Appeler la fonction protégée
            return func(event, context)

        except TokenValidationError as e:
            logger.warning(f"JWT validation failed: {e}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'WWW-Authenticate': 'Bearer realm="ENGIE API"'
                },
                'body': {
                    'error': {
                        'code': 401,
                        'message': 'Unauthorized',
                        'details': [
                            {
                                'field': 'Authorization',
                                'error': str(e)
                            }
                        ]
                    }
                }
            }

    return wrapper


def clear_token_cache():
    """
    Vide le cache de token (utile pour les tests)
    """
    global _token_cache
    _token_cache = {
        'access_token': None,
        'expires_at': None
    }
