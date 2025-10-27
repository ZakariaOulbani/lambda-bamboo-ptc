#!/usr/bin/env python3
"""
Script de test pour verifier que le client PTC fonctionne

Ce script teste la connexion a l'API PTC et appelle les endpoints principaux
"""
from src.ptc_client import call_ptc_service


def test_get_all_locations():
    """Test GetAllLocations endpoint"""
    print("1. Test GetAllLocations...")
    data = call_ptc_service('GetAllLocations')
    locations_count = len(data.get('locations', []))
    print(f"   OK - Nombre de locations : {locations_count}")
    assert locations_count > 0, "Aucune location retournee"
    return data


def test_get_location_by_id():
    """Test GetLocationById endpoint"""
    print("\n2. Test GetLocationById...")
    data = call_ptc_service('GetLocationById', {
        'location_name': 'LOC_0001',
        'asset_name': '',
        'circuit_name': ''
    })
    location_name = data['locations'][0]['name']['value']
    print(f"   OK - Location : {location_name}")
    assert location_name == 'LOC_0001', "Location incorrecte"
    return data


def test_get_location_properties_history():
    """Test GetLocationPropertiesHistory endpoint"""
    print("\n3. Test GetLocationPropertiesHistory...")
    data = call_ptc_service('GetLocationPropertyHistory', {
        'location_name': 'LOC_0001',
        'asset_name': '',
        'circuit_name': '',
        'from': '2025-10-18T14:23:45.678Z',
        'to': '2025-10-22T14:23:45.678Z'
    })
    location_name = data['locations'][0]['name']
    print(f"   OK - Historique pour location : {location_name}")
    return data


if __name__ == "__main__":
    print("=== Test du client PTC ===\n")

    try:
        # Test 1
        test_get_all_locations()

        # Test 2
        test_get_location_by_id()

        # Test 3
        test_get_location_properties_history()

        print("\n=== Tous les tests sont passes ===")

    except Exception as e:
        print(f"\n   ERREUR : {e}")
        import traceback
        traceback.print_exc()
