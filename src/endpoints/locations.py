"""
Endpoints pour les locations
- GET /locations
- GET /locations/{location_id}
"""

from datetime import datetime, timezone
from ..models import (
    LocationsListModel,
    LocationHierarchyModel,
    AssetHierarchyModel,
    CircuitHierarchyModel,
    LocationModel,
    AssetModel,
    CircuitModel,
    MeasureModel,
    MeasureTextModel,
    ErrorModel,
    ErrorInfo,
    ErrorDetail
)


def create_mock_measure(value: float) -> MeasureModel:
    """Helper pour créer une mesure mock"""
    return MeasureModel(
        value=value,
        timestamp=datetime.now(timezone.utc).isoformat(),
        quality="1"
    )


def create_mock_operation_mode(mode: str) -> MeasureTextModel:
    """Helper pour créer un operation_mode mock"""
    return MeasureTextModel(
        value=mode,
        timestamp=datetime.now(timezone.utc).isoformat(),
        quality="1"
    )


def get_all_locations() -> LocationsListModel:
    """
    GET /locations
    Retourne toutes les locations avec leur hiérarchie

    TODO: Récupérer depuis PTC
    """
    # Pour l'instant, retourner des données mockées
    mock_locations = LocationsListModel(
        locations=[
            LocationHierarchyModel(
                id="icepark-001",
                name="IcePark Angers",
                assets=[
                    AssetHierarchyModel(
                        id="chiller-001",
                        name="Trane Chiller System",
                        circuits=[
                            CircuitHierarchyModel(
                                id="circuit-s1",
                                name="Water Circuit S1"
                            ),
                            CircuitHierarchyModel(
                                id="circuit-s2",
                                name="Ambient Sensor Zone 1"
                            ),
                            CircuitHierarchyModel(
                                id="circuit-s3",
                                name="Ambient Sensor Zone 2"
                            )
                        ]
                    ),
                    AssetHierarchyModel(
                        id="pv-001",
                        name="Solar Panels",
                        circuits=[]
                    )
                ]
            )
        ]
    )

    return mock_locations


def get_location_by_id(
    location_id: str,
    asset_id: str = None,
    circuit_id: str = None
) -> LocationModel:
    """
    GET /locations/{location_id}
    Retourne les données temps réel d'une location

    Paramètres:
        location_id: ID de la location
        asset_id: (optionnel) Filtrer sur un asset spécifique
        circuit_id: (optionnel) Filtrer sur un circuit spécifique

    TODO: Récupérer depuis PTC et appliquer les filtres
    """
    # Vérifier que la location existe (mock)
    if location_id != "icepark-001":
        raise ValueError(f"Location {location_id} not found")

    # Données mockées temps réel
    mock_location = LocationModel(
        id=location_id,
        grid_power=create_mock_measure(23.5),
        aggregated_power=create_mock_measure(20.1),
        local_generated_power=create_mock_measure(-3.4),
        assets=[
            AssetModel(
                id="chiller-001",
                tempsp=create_mock_measure(7.0),
                deltatempsp=create_mock_measure(0.5),
                temp=create_mock_measure(6.8),
                power=create_mock_measure(15.2),
                humidity=create_mock_measure(45.5),
                quality=create_mock_measure(1),
                availability=create_mock_measure(1),
                operation_mode=create_mock_operation_mode("EXTERNAL"),
                status=create_mock_measure(1),
                circuits=[
                    CircuitModel(
                        id="circuit-s1",
                        tempsp=create_mock_measure(7.0),
                        temp=create_mock_measure(6.9),
                        power=create_mock_measure(8.5),
                        availability=create_mock_measure(1),
                        status=create_mock_measure(1)
                    ),
                    CircuitModel(
                        id="circuit-s2",
                        temp=create_mock_measure(13.4),
                        humidity=create_mock_measure(45.2),
                        quality=create_mock_measure(1)
                    ),
                    CircuitModel(
                        id="circuit-s3",
                        temp=create_mock_measure(13.6),
                        humidity=create_mock_measure(46.1),
                        quality=create_mock_measure(1)
                    )
                ]
            ),
            AssetModel(
                id="pv-001",
                power=create_mock_measure(-3.4),
                status=create_mock_measure(1),
                circuits=[]
            )
        ]
    )

    # TODO: Appliquer les filtres asset_id et circuit_id si fournis
    if asset_id:
        # Filtrer pour ne garder qu'un asset
        mock_location.assets = [
            asset for asset in mock_location.assets
            if asset.id == asset_id
        ]

    if circuit_id and mock_location.assets:
        # Filtrer pour ne garder qu'un circuit
        for asset in mock_location.assets:
            asset.circuits = [
                circuit for circuit in asset.circuits
                if circuit.id == circuit_id
            ]

    return mock_location
