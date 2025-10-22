"""
Endpoints pour les activations
- POST /activations
- GET /activations
"""

from ..models import (
    HierarchicalActivationModel,
    ActivationResponseModel,
    ActivationsListModel
)


def send_activation(activation_data: HierarchicalActivationModel) -> list[ActivationResponseModel]:
    """
    POST /activations
    Envoie des activations vers PTC

    Paramètres:
        activation_data: Données d'activation au format hiérarchique

    Returns:
        Liste des réponses pour chaque activation

    TODO: Envoyer à PTC et gérer les réponses réelles
    """
    responses = []

    # Parcourir toutes les activations et créer des réponses mockées
    for location in activation_data.locations:
        # Activations au niveau location
        for activation in location.activations:
            responses.append(ActivationResponseModel(
                id=activation.id,
                response=200,
                error=None
            ))

        # Activations au niveau asset
        for asset in location.assets:
            for activation in asset.activations:
                responses.append(ActivationResponseModel(
                    id=activation.id,
                    response=200,
                    error=None
                ))

            # Activations au niveau circuit
            for circuit in asset.circuits:
                for activation in circuit.activations:
                    responses.append(ActivationResponseModel(
                        id=activation.id,
                        response=200,
                        error=None
                    ))

    # TODO: Appeler PTC pour chaque activation
    # TODO: Gérer les erreurs (503 si PTC down, 400 si mauvais paramètres, etc.)

    return responses


def get_all_activations(
    activation_status: list[str] = None,
    location_id: str = None,
    asset_id: str = None,
    circuit_id: str = None
) -> list[ActivationsListModel]:
    """
    GET /activations
    Récupère la liste des activations

    Paramètres:
        activation_status: Liste de statuts à filtrer (idle, waiting, active, cancelled, completed)
        location_id: Filtrer sur une location
        asset_id: Filtrer sur un asset
        circuit_id: Filtrer sur un circuit

    TODO: Récupérer depuis PTC avec les bons filtres
    """
    # Données mockées
    mock_activations = [
        ActivationsListModel(
            id="activation-001",
            target_id="circuit-s1",
            target_type="circuit",
            requested_start_time="2025-01-13T12:00:00Z",
            requested_end_time="2025-01-13T12:15:00Z",
            actual_start_time="2025-01-13T12:00:05Z",
            actual_end_time=None,  # En cours
            setpoint=7.5,
            delta_setpoint=0.5,
            activation_status="active"
        ),
        ActivationsListModel(
            id="activation-002",
            target_id="chiller-001",
            target_type="asset",
            requested_start_time="2025-01-13T11:30:00Z",
            requested_end_time="2025-01-13T11:45:00Z",
            actual_start_time="2025-01-13T11:30:02Z",
            actual_end_time="2025-01-13T11:45:01Z",
            setpoint=None,
            delta_setpoint=1.0,
            activation_status="completed"
        )
    ]

    # TODO: Appliquer les filtres activation_status, location_id, asset_id, circuit_id
    filtered_activations = mock_activations

    if activation_status:
        # Logique de filtrage par statut
        filtered_activations = [
            act for act in filtered_activations
            if act.activation_status in activation_status
        ]

    if location_id:
        # Filtrer par location
        pass

    if asset_id:
        filtered_activations = [
            act for act in filtered_activations
            if act.target_id == asset_id or act.target_type != "asset"
        ]

    if circuit_id:
        filtered_activations = [
            act for act in filtered_activations
            if act.target_id == circuit_id or act.target_type != "circuit"
        ]

    return filtered_activations
