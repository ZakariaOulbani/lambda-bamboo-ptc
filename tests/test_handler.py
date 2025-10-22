"""
Tests unitaires pour handler.py - VERSION ACTUELLE

Tests du routing et de la gestion des erreurs du handler principal
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.handler import lambda_handler, create_response, create_error_response
from src.models import LocationsListModel, LocationModel


class TestLambdaHandlerRouting:
    """Tests du routing du handler Lambda"""

    @patch('src.handler.get_all_locations')
    def test_routes_to_get_all_locations(self, mock_get_all_locations):
        """
        Test que GET /locations appelle get_all_locations
        """
        # Arrange
        mock_result = MagicMock(spec=LocationsListModel)
        mock_result.model_dump.return_value = {'locations': []}
        mock_get_all_locations.return_value = mock_result

        event = {
            'httpMethod': 'GET',
            'path': '/locations',
            'queryStringParameters': None,
            'pathParameters': None,
            'body': None
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 200
        mock_get_all_locations.assert_called_once()

    @patch('src.handler.get_location_by_id')
    def test_routes_to_get_location_by_id(self, mock_get_location_by_id):
        """
        Test que GET /locations/{id} appelle get_location_by_id avec le bon ID
        """
        # Arrange
        mock_result = MagicMock(spec=LocationModel)
        mock_result.model_dump.return_value = {'id': 'icepark-001'}
        mock_get_location_by_id.return_value = mock_result

        event = {
            'httpMethod': 'GET',
            'path': '/locations/icepark-001',
            'queryStringParameters': None,
            'pathParameters': {'location_id': 'icepark-001'},
            'body': None
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 200
        mock_get_location_by_id.assert_called_once_with('icepark-001', None, None)

    @patch('src.handler.get_measures_by_location')
    def test_routes_to_get_measures(self, mock_get_measures):
        """
        Test que GET /locations/{id}/measures appelle get_measures_by_location
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {'id': 'icepark-001'}
        mock_get_measures.return_value = mock_result

        event = {
            'httpMethod': 'GET',
            'path': '/locations/icepark-001/measures',
            'queryStringParameters': None,
            'pathParameters': {'location_id': 'icepark-001'},
            'body': None
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 200
        mock_get_measures.assert_called_once()

    @patch('src.handler.send_activation')
    def test_routes_to_send_activation(self, mock_send_activation):
        """
        Test que POST /activations appelle send_activation
        """
        # Arrange
        mock_result = []
        mock_send_activation.return_value = mock_result

        event = {
            'httpMethod': 'POST',
            'path': '/activations',
            'queryStringParameters': None,
            'pathParameters': None,
            'body': json.dumps({
                'locations': [{
                    'id': 'icepark-001',
                    'activations': [],
                    'assets': []
                }]
            })
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 200
        mock_send_activation.assert_called_once()

    @patch('src.handler.get_all_activations')
    def test_routes_to_get_all_activations(self, mock_get_all_activations):
        """
        Test que GET /activations appelle get_all_activations
        """
        # Arrange
        mock_get_all_activations.return_value = []

        event = {
            'httpMethod': 'GET',
            'path': '/activations',
            'queryStringParameters': None,
            'pathParameters': None,
            'body': None
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 200
        mock_get_all_activations.assert_called_once()

    def test_returns_404_for_unknown_path(self):
        """
        Test que le handler retourne 404 pour un path inconnu
        """
        # Arrange
        event = {
            'httpMethod': 'GET',
            'path': '/unknown',
            'queryStringParameters': None,
            'pathParameters': None,
            'body': None
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body

    def test_returns_400_for_invalid_json(self):
        """
        Test que POST /activations retourne 400 pour du JSON invalide
        """
        # Arrange
        event = {
            'httpMethod': 'POST',
            'path': '/activations',
            'queryStringParameters': None,
            'pathParameters': None,
            'body': 'invalid json{'
        }

        # Act
        response = lambda_handler(event, None)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestResponseHelpers:
    """Tests des fonctions de création de réponses"""

    def test_create_response_returns_correct_structure(self):
        """
        Test que create_response retourne la structure correcte
        """
        # Arrange
        body = {'test': 'data'}

        # Act
        response = create_response(200, body)

        # Assert
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert 'body' in response
        assert 'Content-Type' in response['headers']

    # Tests de sérialisation - À implémenter
    # def test_create_response_serializes_pydantic_model(self):
    #     """Test que create_response sérialise un modèle Pydantic"""
    #     pass

    def test_create_error_response_returns_error_structure(self):
        """
        Test que create_error_response retourne une structure d'erreur
        """
        # Act
        response = create_error_response(404, "Not found")

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error']['code'] == 404
        assert body['error']['message'] == "Not found"
