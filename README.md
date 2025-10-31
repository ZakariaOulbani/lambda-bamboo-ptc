# Lambda Bamboo-PTC

Connecteur Lambda entre Bamboo Energy et l'API PTC ThingWorx.

## Prérequis

- Docker
- Docker Compose

Aucune installation locale de Python ou AWS CLI n'est nécessaire. Tout tourne dans des containers.

## Démarrage rapide

1. **Démarrer les services** (LocalStack + environnement de développement):
```bash
docker-compose up -d
```

Cela démarre:
- `localstack`: Émulation AWS (Lambda, CloudWatch, IAM)
- `dev`: Container avec Python, AWS CLI et toutes les dépendances

2. **Déployer la Lambda**:
```bash
./deploy-local.sh
```

3. **Tester l'API**:
```bash
docker-compose exec dev python3 test_lambda.py
```

## Structure du projet

```
lambda-bamboo-ptc/
├── src/
│   ├── handler.py              # Point d'entrée Lambda (routing HTTP)
│   ├── models.py               # Modèles Pydantic
│   ├── ptc_client.py           # Client HTTP pour l'API PTC
│   ├── ptc_transformer.py      # Transformateurs de données PTC
│   └── endpoints/
│       ├── locations.py        # Endpoints locations (GET)
│       ├── measures.py         # Endpoints measures (GET)
│       └── activations.py      # Endpoints activations (GET/POST/PUT)
├── tests/
│   ├── unit/                   # Tests unitaires (avec mocks)
│   │   ├── test_ptc_transformer.py
│   │   ├── test_activations.py
│   │   ├── test_locations.py
│   │   ├── test_measures.py
│   │   └── test_handler.py
│   └── integration/            # Tests d'intégration (API réelle)
│       └── test_ptc_client.py
├── template.yaml               # Template SAM
├── docker-compose.yml          # LocalStack
├── deploy-local.sh             # Script de déploiement
└── requirements.txt
```

## Endpoints disponibles

L'API expose les endpoints suivants:

- `GET /locations` - Liste hiérarchique de toutes les locations (avec assets et circuits)
- `GET /locations/{id}` - Données temps réel d'une location spécifique
- `GET /locations/{id}/measures` - Historique des mesures d'une location
- `POST /activations` - Envoyer des activations vers PTC
- `GET /activations` - Récupérer la liste des activations
- `PUT /locations/{thing_id}/properties/{property_name}` - Modifier une propriété d'un équipement

Exemple d'utilisation du endpoint PUT:
```bash
curl -X PUT http://localhost:4566/restapis/.../locations/CHILLER_0001/properties/power \
  -H "Content-Type: application/json" \
  -d '{"value": 25}'
```

Propriétés modifiables: power, tempsp, deltatempsp, status, operation_mode, availability, humidity, temp, quality

## Mode Mock vs Mode Réel

Le projet peut fonctionner en deux modes:

### Mode Mock (par défaut)
Par défaut, le système utilise des données mockées (pas d'appels à l'API PTC réelle). C'est utile pour le développement et les tests sans dépendre de la disponibilité de PTC.

Dans le `.env`:
```bash
USE_MOCK=true
```

### Mode Réel
Pour utiliser l'API PTC réelle, configurer le `.env` avec:
```bash
PTC_API_URL=https://engie-poc1.cloud.thingworx.com/Thingworx
PTC_API_KEY=votre_api_key_ici
USE_MOCK=false
```

## Commandes utiles

### Développement

Modifier le code dans `src/` puis redéployer:
```bash
./deploy-local.sh
```

### Logs

Logs LocalStack:
```bash
docker-compose logs -f localstack
```

Logs Lambda:
```bash
docker-compose exec dev aws --endpoint-url=http://localstack:4566 logs tail /aws/lambda/bamboo-ptc-connector --follow
```

### Shell interactif

Entrer dans le container de développement:
```bash
docker-compose exec dev bash
```

### Tests

Lancer tous les tests:
```bash
docker-compose exec dev pytest tests/ -v
```

Uniquement les tests unitaires (rapide):
```bash
docker-compose exec dev pytest tests/unit/ -v
```

Uniquement les tests d'intégration (nécessite PTC):
```bash
export USE_MOCK=false
docker-compose exec dev pytest tests/integration/ -v
```

Lancer un fichier spécifique:
```bash
docker-compose exec dev pytest tests/unit/test_locations.py -v
```

Voir la couverture de code:
```bash
docker-compose exec dev pytest tests/ --cov=src --cov-report=term-missing
```

Statistiques actuelles:
- 88 tests au total
- 85 tests unitaires (~0.4s)
- 3 tests d'intégration (~3s si PTC actif)
- Temps d'exécution total: ~3.2s

### Arrêter

```bash
docker-compose down
```

### Rebuild complet

Si vous modifiez le Dockerfile ou requirements.txt:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Déploiement en production

Le déploiement AWS sera géré par l'équipe DevOps avec le template SAM fourni (`template.yaml`).

## Configuration

Variables d'environnement à configurer en production:

### API PTC ThingWorx
- `PTC_API_URL` - URL de l'API PTC ThingWorx
- `PTC_API_KEY` - Clé d'API PTC (à garder secrète)
- `USE_MOCK` - Mode mock (true) ou réel (false)

### Authentification JWT (Document v1.4 pages 30-32)
- `ENGIE_CLIENT_ID` - Client ID OAuth2 ENGIE (fourni par email)
- `ENGIE_CLIENT_SECRET` - Client Secret OAuth2 ENGIE (à garder secret!)
- `ENVIRONMENT` - Environnement (dev ou prod)
- `JWT_AUTHENTICATION_ENABLED` - Activer/désactiver JWT (true/false)

### Autres
- `LOG_LEVEL` - Niveau de log (INFO, DEBUG)

## Authentification JWT

L'API utilise l'authentification JWT conforme au **document v1.4 (pages 30-32)**.

### Configuration des Credentials

1. **Obtenir les credentials ENGIE** (fournis par email):
   - `client_id`
   - `client_secret`

2. **Configurer dans .env**:
```bash
ENGIE_CLIENT_ID=votre_client_id_ici
ENGIE_CLIENT_SECRET=votre_client_secret_ici
ENVIRONMENT=dev  # ou prod
JWT_AUTHENTICATION_ENABLED=true
```

### Obtenir un Token JWT

Pour tester l'authentification:
```bash
python3 test_jwt_auth.py
```

Ou manuellement avec curl:
```bash
# Obtenir un token (DEV)
curl --location 'https://apis-int1.svc.engie-solutions.fr/oauth2/b2b/v1/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'client_id=votre_client_id' \
  --data-urlencode 'client_secret=votre_client_secret' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'scope=apis'

# Réponse:
# {
#   "token_type": "Bearer",
#   "expires_in": 3600,
#   "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
# }
```

### Utiliser le Token JWT

Tous les endpoints nécessitent le header `Authorization`:

```bash
curl -X GET http://localhost:4566/restapis/.../locations \
  -H "Authorization: Bearer votre_token_jwt_ici"
```

### Désactiver JWT (Développement uniquement)

Pour tester sans authentification:
```bash
# Dans .env
JWT_AUTHENTICATION_ENABLED=false
```

**ATTENTION**: Ne JAMAIS désactiver JWT en production!

## Intégration PTC

L'intégration avec PTC ThingWorx a été implémentée et utilise les services suivants:

1. **GetAllLocations** - Récupère la hiérarchie complète locations/assets/circuits
2. **GetLocationById** - Récupère les données temps réel d'une location
3. **GetLocationPropertyHistory** - Récupère l'historique des mesures
4. **Thing SetProperty** - Modifie une propriété d'un équipement (PUT)

Les transformateurs de données (`ptc_transformer.py`) convertissent automatiquement:
- Timestamps Unix (millisecondes) vers format ISO 8601
- Structure imbriquée PTC vers modèles Pydantic
- Gestion des valeurs nulles et des cas limites

Le client PTC (`ptc_client.py`) gère:
- Authentification avec appKey
- Appels POST pour les lectures (services)
- Appels PUT pour les écritures (propriétés)
- Gestion des erreurs HTTP
