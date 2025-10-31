"""
Handler principal de la Lambda
Route les requêtes API Gateway vers les bons endpoints

Authentification JWT conforme au document v1.4 (pages 30-32):
- Tous les endpoints nécessitent un token JWT valide
- Header requis: Authorization: Bearer <token>
- Token obtenu via ENGIE OAuth2 API
"""

import os
import json
import logging
from typing import Dict, Any

from .endpoints.locations import get_all_locations, get_location_by_id
from .endpoints.measures import get_measures_by_location
from .endpoints.activations import send_activation, get_all_activations, set_property
from .auth import validate_jwt_token, TokenValidationError
from .models import (
    HierarchicalActivationModel,
    ErrorModel,
    ErrorInfo,
    ErrorDetail
)

# Configuration du logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_response(status_code: int, body: Any) -> Dict[str, Any]:
    """
    Crée une réponse formatée pour API Gateway

    Args:
        status_code: Code HTTP (200, 400, 404, 500, etc.)
        body: Corps de la réponse (dict ou modèle Pydantic)

    Returns:
        Réponse formatée pour API Gateway
    """
    # Convertir le body en JSON
    if hasattr(body, 'model_dump'):
        # C'est un modèle Pydantic
        body_json = body.model_dump(exclude_none=True)
    elif isinstance(body, list) and len(body) > 0 and hasattr(body[0], 'model_dump'):
        # C'est une liste de modèles Pydantic
        body_json = [item.model_dump(exclude_none=True) for item in body]
    else:
        body_json = body

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS
            'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body_json)
    }


def create_error_response(status_code: int, message: str, details: list = None) -> Dict[str, Any]:
    """
    Crée une réponse d'erreur formatée

    Args:
        status_code: Code HTTP d'erreur
        message: Message d'erreur
        details: Liste de détails d'erreur (optionnel)

    Returns:
        Réponse d'erreur formatée
    """
    error_model = ErrorModel(
        error=ErrorInfo(
            code=status_code,
            message=message,
            details=details or []
        )
    )

    return create_response(status_code, error_model)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Point d'entrée de la Lambda avec authentification JWT

    Conforme au document v1.4 (pages 30-32):
    - Valide le token JWT pour toutes les requêtes (sauf OPTIONS pour CORS)
    - Retourne 401 Unauthorized si le token est invalide ou manquant

    Args:
        event: Événement API Gateway contenant la requête HTTP
        context: Contexte d'exécution Lambda

    Returns:
        Réponse formatée pour API Gateway
    """
    try:
        # Logger l'événement reçu (sans les headers sensibles)
        safe_event = {k: v for k, v in event.items() if k != 'headers'}
        logger.info(f"Received event: {json.dumps(safe_event)}")

        # Extraire les informations de la requête
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        body = event.get('body')

        logger.info(f"{http_method} {path}")

        # Gérer les requêtes OPTIONS pour CORS (pas d'auth requise)
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': ''
            }

        # =====================================================================
        # AUTHENTIFICATION JWT (Document v1.4 pages 30-32)
        # =====================================================================
        # Vérifier si l'authentification JWT est activée
        jwt_enabled = os.getenv('JWT_AUTHENTICATION_ENABLED', 'true').lower() in ('true', '1', 'yes')

        if jwt_enabled:
            try:
                # Valider le token JWT
                token_info = validate_jwt_token(event)
                logger.info(f"JWT token validated for request {http_method} {path}")

                # Ajouter les infos d'auth dans l'event pour les endpoints
                event['auth'] = token_info

            except TokenValidationError as e:
                # Token invalide ou manquant -> 401 Unauthorized
                logger.warning(f"JWT validation failed: {e}")
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'WWW-Authenticate': 'Bearer realm="ENGIE Bamboo-PTC API"',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
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
                    })
                }
        else:
            logger.warning("JWT authentication is DISABLED - for development only!")

        # =====================================================================
        # ROUTING DES ENDPOINTS
        # =====================================================================

        # Router vers le bon endpoint
        # GET /locations
        if path == '/locations' and http_method == 'GET':
            result = get_all_locations()
            return create_response(200, result)

        # GET /locations/{location_id}
        elif path.startswith('/locations/') and http_method == 'GET' and '/measures' not in path:
            location_id = path_params.get('location_id')
            asset_id = query_params.get('asset_id')
            circuit_id = query_params.get('circuit_id')

            if not location_id:
                return create_error_response(
                    400,
                    "Missing location_id parameter",
                    [ErrorDetail(field="location_id", error="Required parameter")]
                )

            try:
                result = get_location_by_id(location_id, asset_id, circuit_id)
                return create_response(200, result)
            except ValueError as e:
                return create_error_response(404, str(e))

        # GET /locations/{location_id}/measures
        elif path.endswith('/measures') and http_method == 'GET':
            location_id = path_params.get('location_id')
            asset_id = query_params.get('asset_id')
            circuit_id = query_params.get('circuit_id')
            from_seconds = int(query_params.get('from', 900))
            to_time = query_params.get('to')
            frequency_seconds = int(query_params.get('frequency', 300))

            if not location_id:
                return create_error_response(
                    400,
                    "Missing location_id parameter"
                )

            try:
                result = get_measures_by_location(
                    location_id,
                    asset_id,
                    circuit_id,
                    from_seconds,
                    to_time,
                    frequency_seconds
                )
                return create_response(200, result)
            except ValueError as e:
                return create_error_response(404, str(e))

        # POST /activations
        elif path == '/activations' and http_method == 'POST':
            if not body:
                return create_error_response(
                    400,
                    "Missing request body"
                )

            try:
                # Parser le body JSON
                body_data = json.loads(body)
                activation_model = HierarchicalActivationModel(**body_data)

                # Envoyer l'activation
                result = send_activation(activation_model)
                return create_response(200, result)

            except json.JSONDecodeError:
                return create_error_response(
                    400,
                    "Invalid JSON in request body"
                )
            except Exception as e:
                logger.error(f"Error parsing activation data: {str(e)}")
                return create_error_response(
                    400,
                    "Invalid activation data",
                    [ErrorDetail(field="body", error=str(e))]
                )

        # GET /activations
        elif path == '/activations' and http_method == 'GET':
            activation_status = query_params.get('activation_status', '').split(',') if query_params.get('activation_status') else None
            location_id = query_params.get('location_id')
            asset_id = query_params.get('asset_id')
            circuit_id = query_params.get('circuit_id')

            result = get_all_activations(activation_status, location_id, asset_id, circuit_id)
            return create_response(200, result)

        # PUT /locations/{thing_id}/properties/{property_name}
        # Route pour modifier une propriété d'un équipement (Thing SetProperty de Postman)
        elif '/properties/' in path and http_method == 'PUT':
            # Récupérer thing_id et property_name depuis les path params
            # URL format: /locations/{thing_id}/properties/{property_name}
            thing_id = path_params.get('thing_id')
            property_name = path_params.get('property_name')

            # Vérifier que les deux sont bien présents
            if not thing_id or not property_name:
                return create_error_response(
                    400,
                    "Missing thing_id or property_name parameter",
                    [ErrorDetail(field="path", error="thing_id and property_name are required")]
                )

            # Vérifier qu'il y a un body
            if not body:
                return create_error_response(
                    400,
                    "Missing request body"
                )

            try:
                # Parser le JSON du body
                body_data = json.loads(body)
                value = body_data.get('value')

                # La valeur est obligatoire dans le body
                if value is None:
                    return create_error_response(
                        400,
                        "Missing 'value' in request body",
                        [ErrorDetail(field="value", error="Required field")]
                    )

                # Appeler la fonction set_property pour faire le boulot
                result = set_property(thing_id, property_name, value)
                return create_response(200, result)

            except json.JSONDecodeError:
                # JSON mal formé
                return create_error_response(
                    400,
                    "Invalid JSON in request body"
                )
            except ValueError as e:
                # Erreur de validation (ex: propriété non autorisée)
                return create_error_response(
                    400,
                    str(e)
                )
            except Exception as e:
                # Erreur inattendue
                logger.error(f"Error setting property: {str(e)}")
                return create_error_response(
                    500,
                    "Error setting property",
                    [ErrorDetail(field="general", error=str(e))]
                )

        # Route non trouvée
        else:
            return create_error_response(
                404,
                f"Route not found: {http_method} {path}"
            )

    except Exception as e:
        # Erreur inattendue
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            "Internal server error",
            [ErrorDetail(field="general", error=str(e))]
        )


# Pour tester localement
if __name__ == '__main__':
    # Exemple d'event pour GET /locations
    test_event = {
        'httpMethod': 'GET',
        'path': '/locations',
        'queryStringParameters': None,
        'pathParameters': None,
        'body': None
    }

    response = lambda_handler(test_event, None)
    print(json.dumps(response, indent=2))
