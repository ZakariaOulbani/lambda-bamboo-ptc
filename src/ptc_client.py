"""
Client pour appeler l'API PTC ThingWorx
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Config PTC - à ne jamais commiter en dur!
PTC_API_URL = os.getenv('PTC_API_URL')
PTC_API_KEY = os.getenv('PTC_API_KEY')


def call_ptc_service(service_name, body=None):
    """
    Fonction pour appeler un service PTC

    Args:
        service_name: nom du service (ex: GetAllLocations, GetLocationById, etc)
        body: paramètres optionnels pour la requête (dict)

    Returns:
        dict: la réponse JSON de PTC
    """
    # Vérifier que les credentials sont bien là
    if not PTC_API_URL or not PTC_API_KEY:
        raise ValueError("PTC_API_URL et PTC_API_KEY doivent être configurés")

    # Construire l'URL complète
    url = f"{PTC_API_URL}/Things/Engie.Locations/Services/{service_name}"

    # Headers comme dans Postman
    headers = {
        'appKey': PTC_API_KEY,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Par défaut body vide si rien passé
    if body is None:
        body = {}

    # Faire l'appel POST
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()  # Lève une exception si erreur HTTP

    return response.json()


def set_ptc_property(thing_name, property_name, value):
    """
    Modifie une propriété d'un Thing dans PTC via PUT
    Basé sur l'endpoint "Thing SetProperty" de la collection Postman

    Args:
        thing_name: nom du Thing (ex: LOC_0001)
        property_name: nom de la propriété (ex: power, tempsp, status)
        value: nouvelle valeur à définir

    Returns:
        dict: confirmation de succès
    """
    # Check credentials
    if not PTC_API_URL or not PTC_API_KEY:
        raise ValueError("PTC_API_URL et PTC_API_KEY doivent être configurés")

    # URL format: /Things/{thing_name}/Properties/{property_name}
    url = f"{PTC_API_URL}/Things/{thing_name}/Properties/{property_name}"

    # Mêmes headers que pour les autres appels
    headers = {
        'appKey': PTC_API_KEY,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Le body contient juste la propriété et sa valeur
    # Ex: {"power": 10}
    payload = {property_name: value}

    # Appel PUT vers PTC
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()

    # Retourner une confirmation
    return {
        "success": True,
        "message": f"Property {property_name} set to {value}"
    }
