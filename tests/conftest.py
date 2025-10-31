"""
Configuration pytest pour les tests unitaires

Ce fichier configure l'environnement de test, notamment:
- Désactivation de l'authentification JWT pour les tests unitaires
- Fixtures communes à tous les tests
"""

import os
import pytest


@pytest.fixture(scope='session', autouse=True)
def disable_jwt_auth():
    """
    Désactive l'authentification JWT pour tous les tests unitaires

    Cette fixture s'exécute automatiquement avant tous les tests
    et désactive la vérification JWT pour simplifier les tests.

    En production, JWT_AUTHENTICATION_ENABLED sera 'true' (par défaut),
    mais dans les tests on le met à 'false' pour éviter d'avoir à
    mocquer les tokens JWT dans chaque test.
    """
    # Sauvegarder la valeur actuelle (si elle existe)
    original_value = os.environ.get('JWT_AUTHENTICATION_ENABLED')

    # Désactiver JWT pour les tests
    os.environ['JWT_AUTHENTICATION_ENABLED'] = 'false'

    # Laisser les tests s'exécuter
    yield

    # Restaurer la valeur originale après les tests
    if original_value is not None:
        os.environ['JWT_AUTHENTICATION_ENABLED'] = original_value
    else:
        os.environ.pop('JWT_AUTHENTICATION_ENABLED', None)


@pytest.fixture
def api_gateway_event():
    """
    Fixture pour créer un événement API Gateway de base

    Returns:
        Dict contenant la structure minimale d'un événement API Gateway
    """
    return {
        'httpMethod': 'GET',
        'path': '/',
        'queryStringParameters': None,
        'pathParameters': None,
        'body': None,
        'headers': {}
    }
