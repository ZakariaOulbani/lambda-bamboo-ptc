"""
Tests unitaires pour activations.py - VERSION ACTUELLE (avec données mockées)
"""

import pytest
from src.endpoints.activations import send_activation, get_all_activations
from src.models import (
    HierarchicalActivationModel,
    LocationsActivationModel,
    AssetsActivationModel,
    CircuitActivationModel,
    ActivationModel,
    ActivationResponseModel
)


class TestSendActivation:
    """Tests pour send_activation (version mock actuelle)"""

    def test_returns_list_of_activation_responses(self):
        """
        Test que send_activation retourne une liste de ActivationResponseModel
        """
        # Arrange
        activation_data = HierarchicalActivationModel(
            locations=[
                LocationsActivationModel(
                    id="icepark-001",
                    activations=[
                        ActivationModel(
                            id="act-001",
                            requested_start_time="2025-01-20T10:00:00Z",
                            requested_end_time="2025-01-20T11:00:00Z",
                            delta_setpoint=2.5
                        )
                    ],
                    assets=[]
                )
            ]
        )

        # Act
        result = send_activation(activation_data)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ActivationResponseModel)

    def test_activation_response_has_correct_id(self):
        """
        Test que la réponse contient le bon ID d'activation
        """
        # Arrange
        activation_data = HierarchicalActivationModel(
            locations=[
                LocationsActivationModel(
                    id="icepark-001",
                    activations=[
                        ActivationModel(
                            id="act-123",
                            requested_start_time="2025-01-20T10:00:00Z",
                            requested_end_time="2025-01-20T11:00:00Z",
                            delta_setpoint=1.0
                        )
                    ],
                    assets=[]
                )
            ]
        )

        # Act
        result = send_activation(activation_data)

        # Assert
        assert result[0].id == "act-123"

    def test_activation_response_has_success_status(self):
        """
        Test que la réponse indique un succès (HTTP 200)
        """
        # Arrange
        activation_data = HierarchicalActivationModel(
            locations=[
                LocationsActivationModel(
                    id="icepark-001",
                    activations=[
                        ActivationModel(
                            id="act-001",
                            requested_start_time="2025-01-20T10:00:00Z",
                            requested_end_time="2025-01-20T11:00:00Z",
                            delta_setpoint=2.0
                        )
                    ],
                    assets=[]
                )
            ]
        )

        # Act
        result = send_activation(activation_data)

        # Assert
        assert result[0].response == 200
        assert result[0].error is None

    def test_handles_multiple_activations(self):
        """
        Test que plusieurs activations retournent plusieurs réponses
        """
        # Arrange
        activation_data = HierarchicalActivationModel(
            locations=[
                LocationsActivationModel(
                    id="icepark-001",
                    activations=[
                        ActivationModel(
                            id="act-001",
                            requested_start_time="2025-01-20T10:00:00Z",
                            requested_end_time="2025-01-20T11:00:00Z",
                            delta_setpoint=2.0
                        ),
                        ActivationModel(
                            id="act-002",
                            requested_start_time="2025-01-20T11:00:00Z",
                            requested_end_time="2025-01-20T12:00:00Z",
                            delta_setpoint=1.5
                        )
                    ],
                    assets=[]
                )
            ]
        )

        # Act
        result = send_activation(activation_data)

        # Assert
        assert len(result) == 2
        assert result[0].id == "act-001"
        assert result[1].id == "act-002"

    # Tests avancés - À implémenter prochainement
    # def test_handles_asset_level_activations(self):
    #     """Test que les activations au niveau asset sont traitées"""
    #     pass

    # def test_handles_circuit_level_activations(self):
    #     """Test que les activations au niveau circuit sont traitées"""
    #     pass

    # def test_handles_mixed_hierarchy_activations(self):
    #     """Test que les activations à plusieurs niveaux sont toutes traitées"""
    #     pass


class TestGetAllActivations:
    """Tests pour get_all_activations (version mock actuelle)"""

    def test_returns_list_of_activations(self):
        """
        Test que get_all_activations retourne une liste
        """
        # Act
        result = get_all_activations()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_returns_two_mock_activations(self):
        """
        Test que la fonction retourne 2 activations mockées
        """
        # Act
        result = get_all_activations()

        # Assert
        assert len(result) == 2

    def test_activation_has_required_fields(self):
        """
        Test que chaque activation a tous les champs requis
        """
        # Act
        result = get_all_activations()

        # Assert
        activation = result[0]
        assert hasattr(activation, 'id')
        assert hasattr(activation, 'target_id')
        assert hasattr(activation, 'target_type')
        assert hasattr(activation, 'requested_start_time')
        assert hasattr(activation, 'requested_end_time')
        assert hasattr(activation, 'activation_status')

    def test_first_activation_is_active(self):
        """
        Test que la première activation mockée a le statut "active"
        """
        # Act
        result = get_all_activations()

        # Assert
        assert result[0].activation_status == "active"
        assert result[0].id == "activation-001"

    def test_second_activation_is_completed(self):
        """
        Test que la deuxième activation mockée a le statut "completed"
        """
        # Act
        result = get_all_activations()

        # Assert
        assert result[1].activation_status == "completed"
        assert result[1].id == "activation-002"

    def test_filter_by_active_status(self):
        """
        Test que le filtre par statut "active" fonctionne
        """
        # Act
        result = get_all_activations(activation_status=["active"])

        # Assert
        assert len(result) == 1
        assert result[0].activation_status == "active"

    # Tests de filtrage avancés - À implémenter
    # def test_filter_by_completed_status(self):
    #     """Test que le filtre par statut "completed" fonctionne"""
    #     pass

    # def test_filter_by_multiple_statuses(self):
    #     """Test que le filtre accepte plusieurs statuts"""
    #     pass

    # def test_filter_by_nonexistent_status_returns_empty(self):
    #     """Test que filtrer par un statut inexistant retourne une liste vide"""
    #     pass

    # def test_filter_by_asset_id(self):
    #     """Test que le filtre asset_id fonctionne"""
    #     pass

    # def test_filter_by_circuit_id(self):
    #     """Test que le filtre circuit_id fonctionne"""
    #     pass

    # def test_model_is_json_serializable(self):
    #     """Test que les activations peuvent être sérialisées en JSON"""
    #     pass
