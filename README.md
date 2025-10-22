# Lambda Bamboo-PTC

Connecteur Lambda entre Bamboo Energy et l'API PTC.

## Prérequis

- Docker
- Docker Compose

Aucune installation locale de Python ou AWS CLI n'est nécessaire. Tout tourne dans des containers.

## Démarrage rapide

1. **Démarrer les services** (LocalStack + environnement de développement) :
```bash
docker-compose up -d
```

Cela démarre :
- `localstack` : Émulation AWS (Lambda, CloudWatch, IAM)
- `dev` : Container avec Python, AWS CLI et toutes les dépendances

2. **Déployer la Lambda** :
```bash
./deploy-local.sh
```

3. **Tester l'API** :
```bash
docker-compose exec dev python3 test_lambda.py
```

## Structure du projet

```
lambda-bamboo-ptc/
├── src/
│   ├── handler.py          # Point d'entrée Lambda
│   ├── models.py           # Modèles Pydantic
│   └── endpoints/
│       ├── locations.py
│       ├── measures.py
│       └── activations.py
├── tests/                  # Tests unitaires
│   ├── test_current_activations.py
│   ├── test_current_locations.py
│   ├── test_current_measures.py
│   └── test_handler.py
├── template.yaml           # Template SAM
├── docker-compose.yml      # LocalStack
├── deploy-local.sh         # Script de déploiement
├── test_lambda.py          # Script de test d'intégration
└── requirements.txt
```

## Endpoints

- `GET /locations` - Liste des locations
- `GET /locations/{id}` - Détails d'une location
- `GET /locations/{id}/measures` - Historique des mesures
- `POST /activations` - Envoyer des activations
- `GET /activations` - Liste des activations

## Commandes utiles

### Développement

Modifier le code dans `src/` puis redéployer :
```bash
./deploy-local.sh
```

### Logs

Logs LocalStack :
```bash
docker-compose logs -f localstack
```

Logs Lambda :
```bash
docker-compose exec dev aws --endpoint-url=http://localstack:4566 logs tail /aws/lambda/bamboo-ptc-connector --follow
```

### Shell interactif

Entrer dans le container de développement :
```bash
docker-compose exec dev bash
```

### Tests d'intégration

```bash
docker-compose exec dev python3 test_lambda.py
```

### Tests unitaires

Lancer tous les tests unitaires :
```bash
docker-compose exec dev pytest tests/ -v
```

Lancer un fichier spécifique :
```bash
docker-compose exec dev pytest tests/test_current_locations.py -v
```

Voir la couverture de code :
```bash
docker-compose exec dev pytest tests/ --cov=src --cov-report=term-missing
```

**Statistiques des tests :**
- 40 tests unitaires actifs
- 4 fichiers de tests (locations, measures, activations, handler)
- 100% de réussite
- 23 tests supplémentaires planifiés

### Arrêter

```bash
docker-compose down
```

### Rebuild complet

Si vous modifiez le Dockerfile ou requirements.txt :
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Déploiement en production

Le déploiement AWS sera géré par l'équipe DevOps avec le template SAM fourni (`template.yaml`).

## Configuration

Variables d'environnement (à ajouter en production) :
- `PTC_API_URL` - URL de l'API PTC
- `PTC_API_KEY` - Clé d'API PTC
- `LOG_LEVEL` - Niveau de log (INFO, DEBUG)

## Notes

Les endpoints retournent actuellement des données mockées. L'intégration réelle avec PTC sera faite en Phase 2.
