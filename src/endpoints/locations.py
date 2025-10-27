"""
Endpoints pour les locations
- GET /locations
- GET /locations/{location_id}
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
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
from ..ptc_client import call_ptc_service
from ..ptc_transformer import transform_get_all_locations, transform_get_location_by_id

load_dotenv()


def _use_mock():
    """Vérifie si on utilise les mocks ou l'API PTC réelle"""
    use_mock = os.getenv('USE_MOCK', 'true').lower()
    return use_mock in ('true', '1', 'yes')


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
    Retourne la liste de toutes les locations avec leur hiérarchie complète
    (locations -> assets -> circuits)
    """
    # Vérifier si on doit utiliser l'API PTC réelle ou les mocks
    if not _use_mock():
        # Appeler l'endpoint GetAllLocations de PTC
        ptc_data = call_ptc_service('GetAllLocations')
        # Transformer les données PTC vers notre format
        return transform_get_all_locations(ptc_data)

    # Mode mock: retourner des données de test pour le dev
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
    Récupère les données temps réel d'une location (power, temp, humidity, etc.)

    Params:
        location_id: ID de la location à récupérer
        asset_id: (optionnel) Filtrer pour ne retourner qu'un asset
        circuit_id: (optionnel) Filtrer pour ne retourner qu'un circuit
    """
    # Mode réel: appeler PTC
    if not _use_mock():
        # Appeler GetLocationById avec les bons paramètres
        ptc_data = call_ptc_service('GetLocationById', {
            'location_name': location_id,
            'asset_name': asset_id or '',  # Envoyer string vide si None
            'circuit_name': circuit_id or ''
        })
        # Transformer la réponse
        location = transform_get_location_by_id(ptc_data)

        # Si on a demandé un asset spécifique, filtrer
        if asset_id:
            location.assets = [a for a in location.assets if a.id == asset_id]

        # Pareil pour les circuits
        if circuit_id and location.assets:
            for asset in location.assets:
                asset.circuits = [c for c in asset.circuits if c.id == circuit_id]

        return location

    # Mode mock - vérifier que la location existe dans nos mocks
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
