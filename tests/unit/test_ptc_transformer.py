"""
Tests unitaires pour ptc_transformer.py

Ces tests vérifient la logique de transformation des données PTC
vers nos modèles Pydantic.
"""

import pytest
from datetime import datetime, timezone
from src.ptc_transformer import (
    convert_timestamp_to_iso,
    extract_ptc_value,
    transform_get_all_locations,
    transform_get_location_by_id,
    transform_get_location_property_history,
    transform_circuit_realtime,
    transform_asset_realtime,
    transform_measure_history,
    transform_measure_text_history
)
from src.models import (
    LocationsListModel,
    LocationModel,
    LocationHistoryModel
)


class TestConvertTimestampToIso:
    """Tests pour convert_timestamp_to_iso"""

    def test_converts_milliseconds_to_iso_format(self):
        """Test conversion timestamp Unix ms vers ISO 8601"""
        # 1729700000000 ms = 2024-10-23 14:20:00 UTC
        result = convert_timestamp_to_iso(1729700000000)
        assert result.endswith('Z')
        assert 'T' in result
        # Vérifier que c'est bien un format ISO valide
        datetime.fromisoformat(result.replace('Z', '+00:00'))

    def test_converts_zero_timestamp(self):
        """Test avec timestamp 0 (epoch)"""
        result = convert_timestamp_to_iso(0)
        assert result == "1970-01-01T00:00:00Z"

    def test_converts_recent_timestamp(self):
        """Test avec un timestamp récent"""
        # 1700000000000 ms = 2023-11-14 22:13:20 UTC
        result = convert_timestamp_to_iso(1700000000000)
        assert result.startswith("2023-11-")
        assert result.endswith('Z')

    def test_result_format_is_correct(self):
        """Test que le format de sortie est correct"""
        result = convert_timestamp_to_iso(1729700000000)
        # Format attendu: YYYY-MM-DDTHH:MM:SSZ
        assert len(result) == 20  # '2024-10-23T14:20:00Z' = 20 caractères
        assert result[10] == 'T'
        assert result[-1] == 'Z'


class TestExtractPtcValue:
    """Tests pour extract_ptc_value"""

    def test_extracts_value_with_time_field(self):
        """Test extraction normale avec field 'time' (temps réel)"""
        ptc_obj = {
            "value": 23.5,
            "time": 1729700000000,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj, use_time=True)

        assert result is not None
        assert result["value"] == 23.5
        assert result["quality"] == "GOOD"
        assert "timestamp" in result
        assert result["timestamp"].endswith('Z')

    def test_extracts_value_with_timestamp_field(self):
        """Test extraction avec field 'timestamp' (historique)"""
        ptc_obj = {
            "value": 15.2,
            "timestamp": 1729700000000,
            "quality": "EXCELLENT"
        }
        result = extract_ptc_value(ptc_obj, use_time=False)

        assert result is not None
        assert result["value"] == 15.2
        assert result["quality"] == "EXCELLENT"
        assert "timestamp" in result

    def test_returns_none_for_null_value(self):
        """Test que None est retourné si value est null"""
        ptc_obj = {
            "value": None,
            "time": 1729700000000,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj)
        assert result is None

    def test_returns_none_for_empty_object(self):
        """Test que None est retourné si l'objet est vide"""
        result = extract_ptc_value(None)
        assert result is None

    def test_returns_none_for_missing_value_key(self):
        """Test que None est retourné si la clé 'value' est absente"""
        ptc_obj = {
            "time": 1729700000000,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj)
        assert result is None

    def test_returns_none_for_missing_timestamp(self):
        """Test que None est retourné si le timestamp est absent"""
        ptc_obj = {
            "value": 23.5,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj, use_time=True)
        assert result is None

    def test_uses_unknown_quality_if_missing(self):
        """Test que 'UNKNOWN' est utilisé si quality est absent"""
        ptc_obj = {
            "value": 23.5,
            "time": 1729700000000
        }
        result = extract_ptc_value(ptc_obj, use_time=True)

        assert result is not None
        assert result["quality"] == "UNKNOWN"

    def test_handles_string_value(self):
        """Test avec une valeur string (ex: operation_mode)"""
        ptc_obj = {
            "value": "EXTERNAL",
            "time": 1729700000000,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj)

        assert result is not None
        assert result["value"] == "EXTERNAL"

    def test_handles_zero_value(self):
        """Test avec valeur 0 (différent de None)"""
        ptc_obj = {
            "value": 0,
            "time": 1729700000000,
            "quality": "GOOD"
        }
        result = extract_ptc_value(ptc_obj)

        assert result is not None
        assert result["value"] == 0


class TestTransformGetAllLocations:
    """Tests pour transform_get_all_locations"""

    def test_transforms_simple_hierarchy(self):
        """Test transformation d'une hiérarchie simple"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "name": "Test Location",
                    "assets": []
                }
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert isinstance(result, LocationsListModel)
        assert len(result.locations) == 1
        assert result.locations[0].id == "LOC_001"
        assert result.locations[0].name == "Test Location"
        assert len(result.locations[0].assets) == 0

    def test_handles_name_as_dict(self):
        """Test quand le nom est un objet {"value": "..."}"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "name": {"value": "Location from Dict"},
                    "assets": []
                }
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert result.locations[0].name == "Location from Dict"

    def test_transforms_complete_hierarchy(self):
        """Test transformation d'une hiérarchie complète avec assets et circuits"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "name": "Test Location",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "name": "Test Asset",
                            "circuits": [
                                {
                                    "id": "CIRCUIT_001",
                                    "name": "Test Circuit"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert len(result.locations) == 1
        assert len(result.locations[0].assets) == 1
        assert result.locations[0].assets[0].id == "ASSET_001"
        assert len(result.locations[0].assets[0].circuits) == 1
        assert result.locations[0].assets[0].circuits[0].id == "CIRCUIT_001"

    def test_handles_multiple_locations(self):
        """Test avec plusieurs locations"""
        ptc_response = {
            "locations": [
                {"id": "LOC_001", "name": "Location 1", "assets": []},
                {"id": "LOC_002", "name": "Location 2", "assets": []},
                {"id": "LOC_003", "name": "Location 3", "assets": []}
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert len(result.locations) == 3
        assert result.locations[0].id == "LOC_001"
        assert result.locations[1].id == "LOC_002"
        assert result.locations[2].id == "LOC_003"

    def test_handles_empty_locations_list(self):
        """Test avec une liste de locations vide"""
        ptc_response = {"locations": []}
        result = transform_get_all_locations(ptc_response)

        assert isinstance(result, LocationsListModel)
        assert len(result.locations) == 0

    def test_handles_missing_locations_key(self):
        """Test quand la clé 'locations' est absente"""
        ptc_response = {}
        result = transform_get_all_locations(ptc_response)

        assert len(result.locations) == 0

    def test_handles_assets_with_dict_names(self):
        """Test assets avec noms en format dict"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "name": "Location",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "name": {"value": "Asset from Dict"},
                            "circuits": []
                        }
                    ]
                }
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert result.locations[0].assets[0].name == "Asset from Dict"

    def test_handles_circuits_with_dict_names(self):
        """Test circuits avec noms en format dict"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "name": "Location",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "name": "Asset",
                            "circuits": [
                                {
                                    "id": "CIRCUIT_001",
                                    "name": {"value": "Circuit from Dict"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = transform_get_all_locations(ptc_response)

        assert result.locations[0].assets[0].circuits[0].name == "Circuit from Dict"


class TestTransformGetLocationById:
    """Tests pour transform_get_location_by_id"""

    def test_transforms_location_with_grid_power(self):
        """Test transformation avec grid_power"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "grid_power": {
                        "value": 23.5,
                        "time": 1729700000000,
                        "quality": "GOOD"
                    },
                    "assets": []
                }
            ]
        }
        result = transform_get_location_by_id(ptc_response)

        assert isinstance(result, LocationModel)
        assert result.id == "LOC_001"
        assert result.grid_power is not None
        assert result.grid_power.value == 23.5

    def test_transforms_location_with_assets(self):
        """Test transformation avec assets"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "power": {
                                "value": 15.2,
                                "time": 1729700000000,
                                "quality": "GOOD"
                            },
                            "circuits": []
                        }
                    ]
                }
            ]
        }
        result = transform_get_location_by_id(ptc_response)

        assert len(result.assets) == 1
        assert result.assets[0].id == "ASSET_001"
        assert result.assets[0].power is not None
        assert result.assets[0].power.value == 15.2

    def test_transforms_complete_location_structure(self):
        """Test transformation complète avec location, assets, circuits"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "grid_power": {"value": 23.5, "time": 1729700000000, "quality": "GOOD"},
                    "aggregated_power": {"value": 20.1, "time": 1729700000000, "quality": "GOOD"},
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "power": {"value": 15.2, "time": 1729700000000, "quality": "GOOD"},
                            "temp": {"value": 6.8, "time": 1729700000000, "quality": "GOOD"},
                            "circuits": [
                                {
                                    "id": "CIRCUIT_001",
                                    "power": {"value": 8.5, "time": 1729700000000, "quality": "GOOD"},
                                    "temp": {"value": 6.9, "time": 1729700000000, "quality": "GOOD"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = transform_get_location_by_id(ptc_response)

        assert result.id == "LOC_001"
        assert result.grid_power.value == 23.5
        assert result.aggregated_power.value == 20.1
        assert len(result.assets) == 1
        assert result.assets[0].power.value == 15.2
        assert result.assets[0].temp.value == 6.8
        assert len(result.assets[0].circuits) == 1
        assert result.assets[0].circuits[0].power.value == 8.5

    def test_handles_empty_assets(self):
        """Test avec assets vide"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "assets": []
                }
            ]
        }
        result = transform_get_location_by_id(ptc_response)

        assert len(result.assets) == 0

    def test_handles_null_measurements(self):
        """Test avec mesures nulles"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "grid_power": {"value": None, "time": 1729700000000, "quality": "BAD"},
                    "assets": []
                }
            ]
        }
        result = transform_get_location_by_id(ptc_response)

        # grid_power devrait être None car value est None
        assert result.grid_power is None


class TestTransformGetLocationPropertyHistory:
    """Tests pour transform_get_location_property_history"""

    def test_transforms_location_history_with_time_series(self):
        """Test transformation avec séries temporelles"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "grid_power": [
                        {"value": 23.5, "timestamp": 1729700000000, "quality": "GOOD"},
                        {"value": 24.0, "timestamp": 1729700300000, "quality": "GOOD"},
                        {"value": 23.8, "timestamp": 1729700600000, "quality": "GOOD"}
                    ],
                    "assets": []
                }
            ]
        }
        result = transform_get_location_property_history(ptc_response)

        assert isinstance(result, LocationHistoryModel)
        assert result.id == "LOC_001"
        assert result.grid_power is not None
        assert len(result.grid_power) == 3
        assert result.grid_power[0].value == 23.5
        assert result.grid_power[1].value == 24.0
        assert result.grid_power[2].value == 23.8

    def test_transforms_asset_history(self):
        """Test transformation historique des assets"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "power": [
                                {"value": 15.0, "timestamp": 1729700000000, "quality": "GOOD"},
                                {"value": 15.5, "timestamp": 1729700300000, "quality": "GOOD"}
                            ],
                            "circuits": []
                        }
                    ]
                }
            ]
        }
        result = transform_get_location_property_history(ptc_response)

        assert len(result.assets) == 1
        assert result.assets[0].id == "ASSET_001"
        assert len(result.assets[0].power) == 2
        assert result.assets[0].power[0].value == 15.0

    def test_transforms_circuit_history(self):
        """Test transformation historique des circuits"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "assets": [
                        {
                            "id": "ASSET_001",
                            "circuits": [
                                {
                                    "id": "CIRCUIT_001",
                                    "temp": [
                                        {"value": 6.8, "timestamp": 1729700000000, "quality": "GOOD"},
                                        {"value": 6.9, "timestamp": 1729700300000, "quality": "GOOD"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = transform_get_location_property_history(ptc_response)

        circuit = result.assets[0].circuits[0]
        assert circuit.id == "CIRCUIT_001"
        assert len(circuit.temp) == 2
        assert circuit.temp[0].value == 6.8

    def test_handles_empty_history(self):
        """Test avec historique vide"""
        ptc_response = {
            "locations": [
                {
                    "id": "LOC_001",
                    "grid_power": [],
                    "assets": []
                }
            ]
        }
        result = transform_get_location_property_history(ptc_response)

        # grid_power devrait être None si la liste est vide
        assert result.grid_power is None


class TestTransformMeasureHistory:
    """Tests pour transform_measure_history"""

    def test_transforms_list_of_measures(self):
        """Test transformation d'une liste de mesures"""
        measures_list = [
            {"value": 23.5, "timestamp": 1729700000000, "quality": "GOOD"},
            {"value": 24.0, "timestamp": 1729700300000, "quality": "GOOD"}
        ]
        result = transform_measure_history(measures_list)

        assert result is not None
        assert len(result) == 2
        assert result[0].value == 23.5
        assert result[1].value == 24.0

    def test_returns_none_for_empty_list(self):
        """Test retourne None pour liste vide"""
        result = transform_measure_history([])
        assert result is None

    def test_returns_none_for_none_input(self):
        """Test retourne None pour None en entrée"""
        result = transform_measure_history(None)
        assert result is None

    def test_filters_out_null_values(self):
        """Test filtre les valeurs nulles"""
        measures_list = [
            {"value": 23.5, "timestamp": 1729700000000, "quality": "GOOD"},
            {"value": None, "timestamp": 1729700300000, "quality": "BAD"},
            {"value": 24.0, "timestamp": 1729700600000, "quality": "GOOD"}
        ]
        result = transform_measure_history(measures_list)

        # Seulement 2 mesures valides
        assert len(result) == 2
        assert result[0].value == 23.5
        assert result[1].value == 24.0


class TestTransformMeasureTextHistory:
    """Tests pour transform_measure_text_history"""

    def test_transforms_text_measures(self):
        """Test transformation mesures textuelles (ex: operation_mode)"""
        measures_list = [
            {"value": "EXTERNAL", "timestamp": 1729700000000, "quality": "GOOD"},
            {"value": "INTERNAL", "timestamp": 1729700300000, "quality": "GOOD"}
        ]
        result = transform_measure_text_history(measures_list)

        assert result is not None
        assert len(result) == 2
        assert result[0].value == "EXTERNAL"
        assert result[1].value == "INTERNAL"

    def test_returns_none_for_empty_list(self):
        """Test retourne None pour liste vide"""
        result = transform_measure_text_history([])
        assert result is None
