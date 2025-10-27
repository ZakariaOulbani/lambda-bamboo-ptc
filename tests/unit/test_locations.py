"""
Tests unitaires pour locations.py - VERSION ACTUELLE (avec données mockées)

Ces tests vérifient le comportement actuel du code sans appels HTTP.
"""

import pytest
from src.endpoints.locations import get_all_locations, get_location_by_id
from src.models import LocationsListModel, LocationModel


class TestGetAllLocations:
    """Tests pour get_all_locations (version mock actuelle)"""

    def test_returns_locations_list_model(self):
        """
        Test que get_all_locations() retourne un LocationsListModel valide
        """
        # Act
        result = get_all_locations()

        # Assert
        assert isinstance(result, LocationsListModel)
        assert hasattr(result, 'locations')
        assert isinstance(result.locations, list)

    def test_returns_icepark_location(self):
        """
        Test que la location IcePark Angers est présente
        """
        # Act
        result = get_all_locations()

        # Assert
        assert len(result.locations) >= 1
        icepark = result.locations[0]
        assert icepark.id == "icepark-001"
        assert icepark.name == "IcePark Angers"

    def test_icepark_has_assets(self):
        """
        Test que IcePark a des assets (chiller et solar panels)
        """
        # Act
        result = get_all_locations()

        # Assert
        icepark = result.locations[0]
        assert len(icepark.assets) == 2

        # Vérifier les IDs des assets
        asset_ids = [asset.id for asset in icepark.assets]
        assert "chiller-001" in asset_ids
        assert "pv-001" in asset_ids

    def test_chiller_has_circuits(self):
        """
        Test que le chiller a 3 circuits
        """
        # Act
        result = get_all_locations()

        # Assert
        icepark = result.locations[0]
        chiller = next(asset for asset in icepark.assets if asset.id == "chiller-001")
        assert len(chiller.circuits) == 3

        # Vérifier les IDs des circuits
        circuit_ids = [circuit.id for circuit in chiller.circuits]
        assert "circuit-s1" in circuit_ids
        assert "circuit-s2" in circuit_ids
        assert "circuit-s3" in circuit_ids

    # Tests de validation avancés - À implémenter
    # def test_circuit_names_are_correct(self):
    #     """Test que les noms des circuits sont corrects"""
    #     pass

    # def test_model_is_json_serializable(self):
    #     """Test que le modèle peut être sérialisé en JSON"""
    #     pass


class TestGetLocationById:
    """Tests pour get_location_by_id (version mock actuelle)"""

    def test_returns_location_model_for_valid_id(self):
        """
        Test que get_location_by_id retourne un LocationModel valide
        """
        # Act
        result = get_location_by_id("icepark-001")

        # Assert
        assert isinstance(result, LocationModel)
        assert result.id == "icepark-001"

    def test_raises_error_for_invalid_location_id(self):
        """
        Test que get_location_by_id lève ValueError pour un ID invalide
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_location_by_id("invalid-id")

        assert "not found" in str(exc_info.value).lower()

    def test_location_has_grid_power(self):
        """
        Test que la location a une mesure grid_power
        """
        # Act
        result = get_location_by_id("icepark-001")

        # Assert
        assert result.grid_power is not None
        assert hasattr(result.grid_power, 'value')
        assert hasattr(result.grid_power, 'timestamp')
        assert hasattr(result.grid_power, 'quality')

    def test_location_has_two_assets(self):
        """
        Test que la location a 2 assets (chiller et pv)
        """
        # Act
        result = get_location_by_id("icepark-001")

        # Assert
        assert len(result.assets) == 2
        asset_ids = [asset.id for asset in result.assets]
        assert "chiller-001" in asset_ids
        assert "pv-001" in asset_ids

    def test_chiller_asset_has_measurements(self):
        """
        Test que l'asset chiller a toutes les mesures attendues
        """
        # Act
        result = get_location_by_id("icepark-001")

        # Assert
        chiller = next(asset for asset in result.assets if asset.id == "chiller-001")
        assert chiller.tempsp is not None
        assert chiller.deltatempsp is not None
        assert chiller.temp is not None
        assert chiller.power is not None
        assert chiller.humidity is not None
        assert chiller.quality is not None
        assert chiller.availability is not None
        assert chiller.operation_mode is not None
        assert chiller.status is not None

    def test_chiller_has_three_circuits(self):
        """
        Test que le chiller a 3 circuits
        """
        # Act
        result = get_location_by_id("icepark-001")

        # Assert
        chiller = next(asset for asset in result.assets if asset.id == "chiller-001")
        assert len(chiller.circuits) == 3

    # Tests de validation des types - À implémenter
    # def test_operation_mode_is_text_measure(self):
    #     """Test que operation_mode est un MeasureTextModel (pas MeasureModel)"""
    #     pass

    def test_filter_by_asset_id(self):
        """
        Test que le filtre asset_id ne retourne que l'asset demandé
        """
        # Act
        result = get_location_by_id("icepark-001", asset_id="chiller-001")

        # Assert
        assert len(result.assets) == 1
        assert result.assets[0].id == "chiller-001"

    # def test_filter_by_asset_id_pv(self):
    #     """Test que le filtre asset_id fonctionne pour les panneaux solaires"""
    #     pass

    def test_filter_by_circuit_id(self):
        """
        Test que le filtre circuit_id ne retourne que le circuit demandé
        """
        # Act
        result = get_location_by_id("icepark-001", circuit_id="circuit-s1")

        # Assert
        chiller = next(asset for asset in result.assets if asset.id == "chiller-001")
        assert len(chiller.circuits) == 1
        assert chiller.circuits[0].id == "circuit-s1"

    def test_filter_by_asset_and_circuit(self):
        """
        Test que les filtres asset_id et circuit_id peuvent être combinés
        """
        # Act
        result = get_location_by_id(
            "icepark-001",
            asset_id="chiller-001",
            circuit_id="circuit-s2"
        )

        # Assert
        assert len(result.assets) == 1
        assert result.assets[0].id == "chiller-001"
        assert len(result.assets[0].circuits) == 1
        assert result.assets[0].circuits[0].id == "circuit-s2"

    # Tests de format et qualité des données - À implémenter
    # def test_timestamps_are_valid_iso_format(self):
    #     """Test que les timestamps sont au format ISO"""
    #     pass

    # def test_quality_values_are_valid(self):
    #     """Test que les valeurs de qualité sont "1" (GOOD)"""
    #     pass
