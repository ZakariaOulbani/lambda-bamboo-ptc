"""
Tests unitaires pour measures.py - VERSION ACTUELLE (avec données mockées)
"""

import pytest
from src.endpoints.measures import get_measures_by_location
from src.models import LocationHistoryModel


class TestGetMeasuresByLocation:
    """Tests pour get_measures_by_location (version mock actuelle)"""

    def test_returns_location_history_model(self):
        """
        Test que get_measures_by_location retourne un LocationHistoryModel valide
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        assert isinstance(result, LocationHistoryModel)
        assert result.id == "icepark-001"

    def test_raises_error_for_invalid_location(self):
        """
        Test que la fonction lève ValueError pour une location invalide
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_measures_by_location("invalid-id")

        assert "not found" in str(exc_info.value).lower()

    def test_grid_power_is_list_of_measures(self):
        """
        Test que grid_power est une liste de mesures (pas une seule mesure)
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        assert isinstance(result.grid_power, list)
        assert len(result.grid_power) > 0
        # Chaque élément doit avoir value, timestamp, quality
        for measure in result.grid_power:
            assert hasattr(measure, 'value')
            assert hasattr(measure, 'timestamp')
            assert hasattr(measure, 'quality')

    def test_returns_three_data_points(self):
        """
        Test que la fonction retourne 3 points de données par défaut
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        assert len(result.grid_power) == 3
        assert len(result.aggregated_power) == 3
        assert len(result.local_generated_power) == 3

    def test_has_two_assets(self):
        """
        Test que l'historique contient 2 assets
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        assert len(result.assets) == 2
        asset_ids = [asset.id for asset in result.assets]
        assert "chiller-001" in asset_ids
        assert "pv-001" in asset_ids

    def test_chiller_has_time_series_for_all_fields(self):
        """
        Test que le chiller a des séries temporelles pour tous les champs
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        chiller = next(asset for asset in result.assets if asset.id == "chiller-001")
        assert isinstance(chiller.tempsp, list)
        assert isinstance(chiller.deltatempsp, list)
        assert isinstance(chiller.temp, list)
        assert isinstance(chiller.power, list)
        assert isinstance(chiller.humidity, list)
        assert isinstance(chiller.quality, list)
        assert isinstance(chiller.availability, list)
        assert isinstance(chiller.status, list)

        # Chaque liste doit avoir 3 éléments
        assert len(chiller.tempsp) == 3
        assert len(chiller.temp) == 3
        assert len(chiller.power) == 3

    def test_chiller_has_three_circuits(self):
        """
        Test que le chiller a 3 circuits avec des séries temporelles
        """
        # Act
        result = get_measures_by_location("icepark-001")

        # Assert
        chiller = next(asset for asset in result.assets if asset.id == "chiller-001")
        assert len(chiller.circuits) == 3

        # Chaque circuit doit avoir des listes de mesures
        circuit_s1 = next(c for c in chiller.circuits if c.id == "circuit-s1")
        assert isinstance(circuit_s1.temp, list)
        assert len(circuit_s1.temp) == 3

    # Tests de validation des données temporelles - À implémenter
    # def test_timestamps_are_chronological(self):
    #     """Test que les timestamps sont dans l'ordre chronologique"""
    #     pass

    # def test_values_have_small_variations(self):
    #     """Test que les valeurs varient légèrement entre les mesures"""
    #     pass

    def test_filter_by_asset_id(self):
        """
        Test que le filtre asset_id ne retourne que l'asset demandé
        """
        # Act
        result = get_measures_by_location("icepark-001", asset_id="chiller-001")

        # Assert
        assert len(result.assets) == 1
        assert result.assets[0].id == "chiller-001"

    # Tests de filtrage et paramètres - À implémenter
    # def test_filter_by_circuit_id(self):
    #     """Test que le filtre circuit_id ne retourne que le circuit demandé"""
    #     pass

    # def test_accepts_time_parameters(self):
    #     """Test que la fonction accepte les paramètres de temps sans erreur"""
    #     pass

    # def test_default_parameters_work(self):
    #     """Test que les paramètres par défaut fonctionnent"""
    #     pass

    # def test_model_is_json_serializable(self):
    #     """Test que le modèle peut être sérialisé en JSON"""
    #     pass
