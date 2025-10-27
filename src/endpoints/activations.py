"""
Endpoints pour les activations

Endpoints disponibles:
- POST /activations : Envoyer des activations vers PTC
- GET /activations : Récupérer la liste des activations
- PUT /locations/{location_id}/properties/{property_name} : Modifier une propriété

TODO: Intégrer les activations avec l'API PTC réelle (actuellement en mock)
"""

import os
from dotenv import load_dotenv
from ..models import (
    HierarchicalActivationModel,
    ActivationResponseModel,
    ActivationsListModel
)
from ..ptc_client import set_ptc_property

load_dotenv()


def _use_mock():
    """Vérifie si on utilise les mocks ou l'API PTC réelle"""
    use_mock = os.getenv('USE_MOCK', 'true').lower()
    return use_mock in ('true', '1', 'yes')


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


def set_property(thing_id: str, property_name: str, value) -> dict:
    """
    PUT /locations/{thing_id}/properties/{property_name}
    Permet de modifier une propriété d'un équipement dans PTC

    Params:
        thing_id: ID du Thing PTC (location, asset, ou circuit)
        property_name: Nom de la propriété à changer
        value: Nouvelle valeur à appliquer

    Returns:
        dict: statut de l'opération
    """
    # Whitelist des propriétés qu'on autorise à modifier
    # Important pour la sécurité, on ne veut pas qu'on puisse tout modifier
    ALLOWED_PROPERTIES = [
        'power',        # puissance
        'tempsp',       # temperature setpoint
        'deltatempsp',  # delta temperature setpoint
        'status',       # statut on/off
        'operation_mode',  # mode de fonctionnement
        'availability', # disponibilité
        'humidity',     # humidité
        'temp',         # température
        'quality'       # qualité
    ]

    # Vérifier que la propriété demandée est dans la liste autorisée
    if property_name not in ALLOWED_PROPERTIES:
        raise ValueError(
            f"Property '{property_name}' is not allowed. "
            f"Allowed properties: {', '.join(ALLOWED_PROPERTIES)}"
        )

    # En mode mock, on simule juste la réponse
    if _use_mock():
        return {
            "success": True,
            "message": f"[MOCK] Property {property_name} of {thing_id} set to {value}",
            "thing_id": thing_id,
            "property_name": property_name,
            "value": value
        }

    # En mode réel, on appelle vraiment l'API PTC
    result = set_ptc_property(thing_id, property_name, value)
    # Enrichir la réponse avec les infos de la requête
    result["thing_id"] = thing_id
    result["property_name"] = property_name
    result["value"] = value

    return result
