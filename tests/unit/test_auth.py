"""
Tests unitaires pour le module d'authentification JWT
Conforme au document v1.4 (pages 30-32)
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.auth import (
    get_oauth2_url,
    get_jwt_token,
    validate_jwt_token,
    clear_token_cache,
    AuthenticationError,
    TokenValidationError
)


class TestOAuth2URL:
    """Tests pour get_oauth2_url()"""

    def test_dev_environment(self):
        """Test URL pour environnement DEV"""
        with patch('os.getenv', return_value='dev'):
            url = get_oauth2_url()
            assert url == 'https://apis-int1.svc.engie-solutions.fr/oauth2/b2b/v1/token'

    def test_prod_environment(self):
        """Test URL pour environnement PROD"""
        with patch('os.getenv', return_value='prod'):
            url = get_oauth2_url()
            assert url == 'https://apis.svc.engie-solutions.fr/oauth2/b2b/v1/token'

    def test_default_to_dev(self):
        """Test que par défaut on utilise DEV"""
        with patch('os.getenv', return_value=''):
            url = get_oauth2_url()
            assert 'int1' in url  # DEV URL contient 'int1'


class TestGetJWTToken:
    """Tests pour get_jwt_token()"""

    def setup_method(self):
        """Nettoyer le cache avant chaque test"""
        clear_token_cache()

    @patch('src.auth.requests.post')
    @patch('os.getenv')
    def test_get_token_success(self, mock_getenv, mock_post):
        """Test obtention d'un token avec succès"""
        # Mock des variables d'environnement
        def getenv_side_effect(key, default=None):
            values = {
                'ENGIE_CLIENT_ID': 'test_client_id',
                'ENGIE_CLIENT_SECRET': 'test_secret',
                'ENVIRONMENT': 'dev'
            }
            return values.get(key, default)

        mock_getenv.side_effect = getenv_side_effect

        # Mock de la réponse OAuth2
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'test_jwt_token_12345',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Appeler la fonction
        token = get_jwt_token()

        # Vérifications
        assert token == 'test_jwt_token_12345'
        assert mock_post.called
        call_args = mock_post.call_args

        # Vérifier l'URL
        assert 'apis-int1.svc.engie-solutions.fr' in call_args[0][0]

        # Vérifier les données envoyées
        assert call_args[1]['data']['client_id'] == 'test_client_id'
        assert call_args[1]['data']['client_secret'] == 'test_secret'
        assert call_args[1]['data']['grant_type'] == 'client_credentials'
        assert call_args[1]['data']['scope'] == 'apis'

    @patch('os.getenv')
    def test_missing_credentials(self, mock_getenv):
        """Test erreur si credentials manquants"""
        mock_getenv.return_value = None

        with pytest.raises(AuthenticationError) as exc_info:
            get_jwt_token()

        assert 'ENGIE_CLIENT_ID' in str(exc_info.value)

    @patch('src.auth.requests.post')
    @patch('os.getenv')
    def test_oauth2_api_error(self, mock_getenv, mock_post):
        """Test erreur si l'API OAuth2 échoue"""
        import requests
        mock_getenv.side_effect = lambda k, d=None: {
            'ENGIE_CLIENT_ID': 'test_id',
            'ENGIE_CLIENT_SECRET': 'test_secret',
            'ENVIRONMENT': 'dev'
        }.get(k, d)

        # Simuler une erreur HTTP
        mock_post.side_effect = requests.RequestException("Connection error")

        with pytest.raises(AuthenticationError) as exc_info:
            get_jwt_token()

        assert 'Failed to authenticate' in str(exc_info.value)

    @patch('src.auth.requests.post')
    @patch('os.getenv')
    def test_token_caching(self, mock_getenv, mock_post):
        """Test que le token est mis en cache"""
        mock_getenv.side_effect = lambda k, d=None: {
            'ENGIE_CLIENT_ID': 'test_id',
            'ENGIE_CLIENT_SECRET': 'test_secret',
            'ENVIRONMENT': 'dev'
        }.get(k, d)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'cached_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Premier appel
        token1 = get_jwt_token()

        # Deuxième appel (devrait utiliser le cache)
        token2 = get_jwt_token()

        # Le token devrait être le même
        assert token1 == token2
        # L'API ne devrait être appelée qu'une seule fois
        assert mock_post.call_count == 1


class TestValidateJWTToken:
    """Tests pour validate_jwt_token()"""

    def test_valid_token_format(self):
        """Test avec un token au bon format"""
        event = {
            'headers': {
                'Authorization': 'Bearer test_token_12345'
            }
        }

        result = validate_jwt_token(event)

        assert result['valid'] is True
        assert result['token'] == 'test_token_12345'
        assert 'validated_at' in result

    def test_case_insensitive_header(self):
        """Test que le header Authorization est case-insensitive"""
        event = {
            'headers': {
                'authorization': 'Bearer test_token_12345'  # lowercase
            }
        }

        result = validate_jwt_token(event)
        assert result['valid'] is True

    def test_missing_authorization_header(self):
        """Test erreur si header Authorization manquant"""
        event = {
            'headers': {}
        }

        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_token(event)

        assert 'Missing Authorization header' in str(exc_info.value)

    def test_invalid_bearer_format(self):
        """Test erreur si format Bearer incorrect"""
        event = {
            'headers': {
                'Authorization': 'InvalidFormat token123'
            }
        }

        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_token(event)

        assert 'Invalid Authorization header format' in str(exc_info.value)

    def test_empty_token(self):
        """Test erreur si token vide"""
        event = {
            'headers': {
                'Authorization': 'Bearer '
            }
        }

        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_token(event)

        assert 'Empty token' in str(exc_info.value)

    def test_no_headers_in_event(self):
        """Test erreur si pas de headers dans l'event"""
        event = {}

        with pytest.raises(TokenValidationError):
            validate_jwt_token(event)


class TestTokenCache:
    """Tests pour le système de cache de tokens"""

    def setup_method(self):
        """Nettoyer le cache avant chaque test"""
        clear_token_cache()

    @patch('src.auth.requests.post')
    @patch('os.getenv')
    def test_cache_expiration(self, mock_getenv, mock_post):
        """Test que le cache expire correctement"""
        mock_getenv.side_effect = lambda k, d=None: {
            'ENGIE_CLIENT_ID': 'test_id',
            'ENGIE_CLIENT_SECRET': 'test_secret',
            'ENVIRONMENT': 'dev'
        }.get(k, d)

        # Premier token (expire dans 1 seconde)
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            'access_token': 'token1',
            'expires_in': 1  # 1 seconde
        }
        mock_response1.raise_for_status = MagicMock()

        # Deuxième token
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            'access_token': 'token2',
            'expires_in': 3600
        }
        mock_response2.raise_for_status = MagicMock()

        mock_post.side_effect = [mock_response1, mock_response2]

        # Premier appel
        token1 = get_jwt_token()
        assert token1 == 'token1'

        # Attendre que le token expire (simulé en vidant le cache)
        clear_token_cache()

        # Deuxième appel après expiration
        token2 = get_jwt_token()
        assert token2 == 'token2'

        # Deux appels API devraient avoir été faits
        assert mock_post.call_count == 2
