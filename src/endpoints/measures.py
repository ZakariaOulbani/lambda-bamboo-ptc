"""
Endpoint pour les mesures historiques
- GET /locations/{location_id}/measures
"""

from datetime import datetime, timezone, timedelta
from ..models import (
    LocationHistoryModel,
    AssetHistoryModel,
    CircuitHistoryModel,
    MeasureModel,
    MeasureTextModel
)


def create_mock_measure_series(base_value: float, count: int = 3) -> list[MeasureModel]:
    """Helper pour créer une série de mesures mock"""
    measures = []
    now = datetime.now(timezone.utc)

    for i in range(count):
        measures.append(MeasureModel(
            value=base_value + (i * 0.1),  # Légère variation
            timestamp=(now - timedelta(minutes=(count - i - 1) * 5)).isoformat(),
            quality="1"
        ))

    return measures


def get_measures_by_location(
    location_id: str,
    asset_id: str = None,
    circuit_id: str = None,
    from_seconds: int = 900,  # 15 minutes par défaut
    to_time: str = None,
    frequency_seconds: int = 300  # 5 minutes par défaut
) -> LocationHistoryModel:
    """
    GET /locations/{location_id}/measures
    Retourne les données historiques d'une location

    Paramètres:
        location_id: ID de la location
        asset_id: (optionnel) Filtrer sur un asset
        circuit_id: (optionnel) Filtrer sur un circuit
        from_seconds: Nombre de secondes depuis maintenant
        to_time: Date/heure de fin (ISO string)
        frequency_seconds: Intervalle entre les mesures

    TODO: Récupérer depuis PTC avec les bons paramètres de temps
    """
    # Vérifier que la location existe (mock)
    if location_id != "icepark-001":
        raise ValueError(f"Location {location_id} not found")

    # Calculer le nombre de points de données
    # Pour simplifier, on fait 3 points
    num_points = 3

    # Données mockées historiques
    mock_history = LocationHistoryModel(
        id=location_id,
        grid_power=create_mock_measure_series(23.5, num_points),
        aggregated_power=create_mock_measure_series(20.1, num_points),
        local_generated_power=create_mock_measure_series(-3.4, num_points),
        assets=[
            AssetHistoryModel(
                id="chiller-001",
                tempsp=create_mock_measure_series(7.0, num_points),
                deltatempsp=create_mock_measure_series(0.5, num_points),
                temp=create_mock_measure_series(6.8, num_points),
                power=create_mock_measure_series(15.2, num_points),
                humidity=create_mock_measure_series(45.5, num_points),
                quality=create_mock_measure_series(1, num_points),
                availability=create_mock_measure_series(1, num_points),
                status=create_mock_measure_series(1, num_points),
                circuits=[
                    CircuitHistoryModel(
                        id="circuit-s1",
                        tempsp=create_mock_measure_series(7.0, num_points),
                        temp=create_mock_measure_series(6.9, num_points),
                        power=create_mock_measure_series(8.5, num_points),
                        availability=create_mock_measure_series(1, num_points),
                        status=create_mock_measure_series(1, num_points)
                    ),
                    CircuitHistoryModel(
                        id="circuit-s2",
                        temp=create_mock_measure_series(13.4, num_points),
                        humidity=create_mock_measure_series(45.2, num_points),
                        quality=create_mock_measure_series(1, num_points)
                    ),
                    CircuitHistoryModel(
                        id="circuit-s3",
                        temp=create_mock_measure_series(13.6, num_points),
                        humidity=create_mock_measure_series(46.1, num_points),
                        quality=create_mock_measure_series(1, num_points)
                    )
                ]
            ),
            AssetHistoryModel(
                id="pv-001",
                power=create_mock_measure_series(-3.4, num_points),
                status=create_mock_measure_series(1, num_points),
                circuits=[]
            )
        ]
    )

    # TODO: Appliquer les filtres asset_id et circuit_id
    if asset_id:
        mock_history.assets = [
            asset for asset in mock_history.assets
            if asset.id == asset_id
        ]

    if circuit_id and mock_history.assets:
        for asset in mock_history.assets:
            asset.circuits = [
                circuit for circuit in asset.circuits
                if circuit.id == circuit_id
            ]

    return mock_history
