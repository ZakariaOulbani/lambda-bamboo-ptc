"""
Endpoint pour les mesures historiques
- GET /locations/{location_id}/measures
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from ..models import (
    LocationHistoryModel,
    AssetHistoryModel,
    CircuitHistoryModel,
    MeasureModel,
    MeasureTextModel
)
from ..ptc_client import call_ptc_service
from ..ptc_transformer import transform_get_location_property_history

load_dotenv()


def _use_mock():
    """Vérifie si on utilise les mocks ou l'API PTC réelle"""
    use_mock = os.getenv('USE_MOCK', 'true').lower()
    return use_mock in ('true', '1', 'yes')


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
    from_seconds: int = 900,  # Par défaut 15 minutes
    to_time: str = None,
    frequency_seconds: int = 300  # Par défaut 5 minutes
) -> LocationHistoryModel:
    """
    GET /locations/{location_id}/measures
    Récupère l'historique des mesures pour une location

    Params:
        location_id: ID de la location
        asset_id: (optionnel) Filtrer sur un asset spécifique
        circuit_id: (optionnel) Filtrer sur un circuit spécifique
        from_seconds: Nombre de secondes en arrière depuis maintenant (défaut: 900 = 15min)
        to_time: Date/heure de fin au format ISO (si None, utilise maintenant)
        frequency_seconds: Intervalle entre les points de données (défaut: 300 = 5min)
    """
    # Mode réel: appeler PTC
    if not _use_mock():
        now = datetime.now(timezone.utc)

        # Calculer la date de fin
        if to_time:
            # Parser la date ISO fournie
            to_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00'))
        else:
            # Sinon utiliser maintenant
            to_dt = now

        # Calculer la date de début en soustrayant from_seconds
        from_dt = to_dt - timedelta(seconds=from_seconds)

        # Convertir en format ISO que PTC attend (avec Z à la fin)
        from_iso = from_dt.isoformat().replace('+00:00', 'Z')
        to_iso = to_dt.isoformat().replace('+00:00', 'Z')

        ptc_data = call_ptc_service('GetLocationPropertyHistory', {
            'location_name': location_id,
            'asset_name': asset_id or '',
            'circuit_name': circuit_id or '',
            'from': from_iso,
            'to': to_iso
        })

        history = transform_get_location_property_history(ptc_data)

        # Appliquer les filtres
        if asset_id:
            history.assets = [a for a in history.assets if a.id == asset_id]

        if circuit_id and history.assets:
            for asset in history.assets:
                asset.circuits = [c for c in asset.circuits if c.id == circuit_id]

        return history

    # Mode mock - vérifier que la location existe
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
