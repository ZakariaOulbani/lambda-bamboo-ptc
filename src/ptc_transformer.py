"""
Transformateurs pour convertir les réponses PTC vers nos modèles Pydantic

Les données de PTC arrivent dans un format assez bizarre avec des timestamps
en millisecondes et des valeurs imbriquées, il faut tout transformer pour que
ça colle avec nos modèles.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.models import (
    LocationsListModel, LocationHierarchyModel, AssetHierarchyModel, CircuitHierarchyModel,
    LocationModel, AssetModel, CircuitModel,
    MeasureModel, MeasureTextModel,
    LocationHistoryModel, AssetHistoryModel, CircuitHistoryModel
)


def convert_timestamp_to_iso(timestamp_ms):
    """
    Convertit un timestamp Unix en millisecondes vers une string ISO 8601

    PTC envoie des timestamps genre 1729700000000 (en ms)
    On veut du ISO genre "2025-10-23T14:20:00Z"
    """
    ts = timestamp_ms / 1000.0  # Convertir ms en secondes
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    # Remplacer +00:00 par Z pour format ISO strict
    return dt.isoformat().replace('+00:00', 'Z')


def extract_ptc_value(ptc_obj, use_time=True):
    """
    Extrait une valeur depuis un objet PTC et la convertit au bon format

    Args:
        ptc_obj: l'objet PTC (dict avec value, time/timestamp, quality)
        use_time: True pour temps réel (field "time"), False pour historique (field "timestamp")

    Returns:
        dict avec timestamp ISO, value, quality OU None si pas de données
    """
    # Si l'objet est None ou vide, on renvoie None
    if not ptc_obj:
        return None

    # Vérifier qu'il y a bien une valeur
    if "value" not in ptc_obj or ptc_obj["value"] is None:
        return None

    # Différence entre temps réel et historique: le nom du champ timestamp change
    time_field = "time" if use_time else "timestamp"
    timestamp_ms = ptc_obj.get(time_field)

    if not timestamp_ms:
        return None

    # Construire l'objet de retour
    return {
        "timestamp": convert_timestamp_to_iso(timestamp_ms),
        "value": ptc_obj["value"],
        "quality": ptc_obj.get("quality", "UNKNOWN")  # Par défaut UNKNOWN si absent
    }


# === Transformation GetAllLocations ===
def transform_get_all_locations(ptc_response):
    """
    Transforme la hiérarchie complète des locations
    PTC retourne une structure locations -> assets -> circuits
    """
    locations = []

    # Parcourir toutes les locations
    for loc in ptc_response.get("locations", []):
        # le nom peut être soit une string, soit un objet avec {"value": "..."}
        # Il faut gérer les 2 cas
        name = loc.get("name")
        if isinstance(name, dict):
            name = name.get("value", "")

        # Parcourir les assets de la location
        assets = []
        for asset in loc.get("assets", []):
            asset_name = asset.get("name")
            if isinstance(asset_name, dict):
                asset_name = asset_name.get("value", "")

            # Parcourir les circuits de l'asset
            circuits = []
            for circuit in asset.get("circuits", []):
                circuit_name = circuit.get("name")
                if isinstance(circuit_name, dict):
                    circuit_name = circuit_name.get("value", "")

                circuits.append(CircuitHierarchyModel(
                    id=circuit.get("id", ""),
                    name=circuit_name
                ))

            assets.append(AssetHierarchyModel(
                id=asset.get("id", ""),
                name=asset_name,
                circuits=circuits
            ))

        locations.append(LocationHierarchyModel(
            id=loc.get("id", ""),
            name=name,
            assets=assets
        ))

    return LocationsListModel(locations=locations)


# Transformation GetLocationById (temps réel)
def transform_circuit_realtime(circuit_data):
    """Convertit un circuit temps réel"""
    return CircuitModel(
        id=circuit_data.get("id", ""),
        tempsp=extract_ptc_value(circuit_data.get("tempsp")),
        deltatempsp=extract_ptc_value(circuit_data.get("deltatempsp")),
        temp=extract_ptc_value(circuit_data.get("temp")),
        power=extract_ptc_value(circuit_data.get("power")),
        humidity=extract_ptc_value(circuit_data.get("humidity")),
        quality=extract_ptc_value(circuit_data.get("quality")),
        availability=extract_ptc_value(circuit_data.get("availability")),
        operation_mode=extract_ptc_value(circuit_data.get("operation_mode")),
        status=extract_ptc_value(circuit_data.get("status"))
    )


def transform_asset_realtime(asset_data):
    """Convertit un asset temps réel"""
    circuits = []
    for c in asset_data.get("circuits", []):
        circuits.append(transform_circuit_realtime(c))

    return AssetModel(
        id=asset_data.get("id", ""),
        tempsp=extract_ptc_value(asset_data.get("tempsp")),
        deltatempsp=extract_ptc_value(asset_data.get("deltatempsp")),
        temp=extract_ptc_value(asset_data.get("temp")),
        power=extract_ptc_value(asset_data.get("power")),
        humidity=extract_ptc_value(asset_data.get("humidity")),
        quality=extract_ptc_value(asset_data.get("quality")),
        availability=extract_ptc_value(asset_data.get("availability")),
        operation_mode=extract_ptc_value(asset_data.get("operation_mode")),
        status=extract_ptc_value(asset_data.get("status")),
        circuits=circuits
    )


def transform_get_location_by_id(ptc_response):
    """
    Transforme les données temps réel d'une location
    PTC retourne un tableau, on prend le premier élément
    """
    loc = ptc_response.get("locations", [{}])[0]

    assets = []
    for a in loc.get("assets", []):
        assets.append(transform_asset_realtime(a))

    return LocationModel(
        id=loc.get("id", ""),
        grid_power=extract_ptc_value(loc.get("grid_power")),
        aggregated_power=extract_ptc_value(loc.get("aggregated_power")),
        local_generated_power=extract_ptc_value(loc.get("local_generated_power")),
        assets=assets
    )


# Transformation GetLocationPropertyHistory (historique)
def transform_measure_history(measures_list):
    """Transforme une liste de mesures historiques"""
    if not measures_list:
        return None

    result = []
    for m in measures_list:
        converted = extract_ptc_value(m, use_time=False)
        if converted:
            result.append(MeasureModel(**converted))

    return result if result else None


def transform_measure_text_history(measures_list):
    """Transforme une liste de mesures textuelles historiques"""
    if not measures_list:
        return None

    result = []
    for m in measures_list:
        converted = extract_ptc_value(m, use_time=False)
        if converted:
            result.append(MeasureTextModel(**converted))

    return result if result else None


def transform_circuit_history(circuit_data):
    """Convertit un circuit historique"""
    return CircuitHistoryModel(
        id=circuit_data.get("id", ""),
        tempsp=transform_measure_history(circuit_data.get("tempsp")),
        deltatempsp=transform_measure_history(circuit_data.get("deltatempsp")),
        temp=transform_measure_history(circuit_data.get("temp")),
        power=transform_measure_history(circuit_data.get("power")),
        humidity=transform_measure_history(circuit_data.get("humidity")),
        quality=transform_measure_history(circuit_data.get("quality")),
        availability=transform_measure_history(circuit_data.get("availability")),
        operation_mode=transform_measure_text_history(circuit_data.get("operation_mode")),
        status=transform_measure_history(circuit_data.get("status"))
    )


def transform_asset_history(asset_data):
    """Convertit un asset historique"""
    circuits = []
    for c in asset_data.get("circuits", []):
        circuits.append(transform_circuit_history(c))

    return AssetHistoryModel(
        id=asset_data.get("id", ""),
        tempsp=transform_measure_history(asset_data.get("tempsp")),
        deltatempsp=transform_measure_history(asset_data.get("deltatempsp")),
        temp=transform_measure_history(asset_data.get("temp")),
        power=transform_measure_history(asset_data.get("power")),
        humidity=transform_measure_history(asset_data.get("humidity")),
        quality=transform_measure_history(asset_data.get("quality")),
        availability=transform_measure_history(asset_data.get("availability")),
        operation_mode=transform_measure_text_history(asset_data.get("operation_mode")),
        status=transform_measure_history(asset_data.get("status")),
        circuits=circuits
    )


def transform_get_location_property_history(ptc_response):
    """Transforme l'historique d'une location"""
    loc = ptc_response.get("locations", [{}])[0]

    assets = []
    for a in loc.get("assets", []):
        assets.append(transform_asset_history(a))

    return LocationHistoryModel(
        id=loc.get("id", ""),
        grid_power=transform_measure_history(loc.get("grid_power")),
        aggregated_power=transform_measure_history(loc.get("aggregated_power")),
        local_generated_power=transform_measure_history(loc.get("local_generated_power")),
        assets=assets
    )
