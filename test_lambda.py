#!/usr/bin/env python3
"""Script de test pour invoquer la Lambda localement"""
import json
import boto3
import os

# Configuration LocalStack
# Utilise 'localstack' si on est dans Docker, sinon 'localhost'
endpoint = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
client = boto3.client(
    'lambda',
    endpoint_url=endpoint,
    region_name='eu-west-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def test_endpoint(path, method='GET', body=None, path_params=None):
    """Teste un endpoint de la Lambda"""

    # Construction du payload au format API Gateway v1
    payload = {
        "httpMethod": method,
        "path": path,
        "headers": {
            "Content-Type": "application/json"
        },
        "queryStringParameters": None,
        "pathParameters": path_params
    }

    if body:
        payload["body"] = json.dumps(body)

    print(f"\n{'='*60}")
    print(f"{method} {path}")
    print(f"{'='*60}")

    try:
        response = client.invoke(
            FunctionName='bamboo-ptc-connector',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())
        print(f"Status: {result.get('statusCode', 'N/A')}")
        print(f"Response:\n{json.dumps(result.get('body'), indent=2)}")

    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    # Test des différents endpoints
    print("\n Tests des endpoints Lambda\n")

    # GET /locations
    test_endpoint("/locations", "GET")

    # GET /locations/icepark-001
    test_endpoint("/locations/icepark-001", "GET", path_params={"location_id": "icepark-001"})

    # GET /locations/icepark-001/measures
    test_endpoint("/locations/icepark-001/measures", "GET", path_params={"location_id": "icepark-001"})

    # GET /activations
    test_endpoint("/activations", "GET")

    # POST /activations
    test_endpoint("/activations", "POST", {
        "locations": [{
            "id": "icepark-001",
            "activations": [],
            "assets": [{
                "id": "chiller-001",
                "activations": [{
                    "id": "activation-test-001",
                    "requested_start_time": "2025-01-15T10:00:00Z",
                    "requested_end_time": "2025-01-15T12:00:00Z",
                    "setpoint": 7.0,
                    "delta_setpoint": 0.5
                }],
                "circuits": [{
                    "id": "circuit-s1",
                    "activations": [{
                        "id": "activation-test-002",
                        "requested_start_time": "2025-01-15T10:00:00Z",
                        "requested_end_time": "2025-01-15T12:00:00Z",
                        "delta_setpoint": 1.0
                    }]
                }]
            }]
        }]
    })

    print("\n Tests terminés\n")
