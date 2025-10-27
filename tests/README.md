# Tests Directory

Organisation des tests pour le projet lambda-bamboo-ptc.

## Structure

```
tests/
├── README.md
├── __init__.py
├── unit/                        # Tests unitaires (avec mocks)
│   ├── __init__.py
│   ├── test_ptc_transformer.py  # Transformateurs de données PTC
│   ├── test_activations.py      # Endpoints activations
│   ├── test_handler.py          # Handler HTTP (routing)
│   ├── test_locations.py        # Endpoints locations
│   └── test_measures.py         # Endpoints measures
└── integration/                 # Tests d'intégration (API réelle)
    ├── __init__.py
    └── test_ptc_client.py       # Client PTC avec appels réels
```

## Types de tests

### Tests Unitaires (dossier unit/)

Ces tests utilisent des données mockées et ne font aucun appel réseau. Ils sont rapides (< 1s) et testent la logique isolée de chaque fonction.

Caractéristiques:
- Aucune dépendance externe
- Pas d'appels réseau
- Utilise des fixtures et des mocks
- Exécution très rapide

Exemple: les tests du transformateur PTC qui convertit les timestamps et extrait les valeurs.

### Tests d'Intégration (dossier integration/)

Ces tests appellent l'API PTC réelle. Ils nécessitent des credentials valides et peuvent échouer si le service est indisponible.

Caractéristiques:
- Appelle les vrais endpoints PTC
- Plus lents (~3s)
- Nécessite PTC_API_URL et PTC_API_KEY dans .env
- Peut échouer si PTC est down

Important: ces tests sont marqués avec USE_MOCK=false pour forcer l'utilisation de l'API réelle.

## Lancer les tests

Tous les tests:
```bash
pytest tests/ -v
```

Uniquement les tests unitaires (rapide):
```bash
pytest tests/unit/ -v
```

Uniquement les tests d'intégration:
```bash
# Attention: nécessite des credentials PTC valides
export USE_MOCK=false
pytest tests/integration/ -v
```

Un fichier spécifique:
```bash
pytest tests/unit/test_ptc_transformer.py -v
```

Avec couverture de code:
```bash
pytest tests/ --cov=src --cov-report=term
```

## Statistiques actuelles

Au total on a 88 tests qui s'exécutent en ~3.2s:
- Tests unitaires: 85 tests (~0.4s)
- Tests d'intégration: 3 tests (~3s si PTC actif)

## Conventions de nommage

Fichiers de tests:
- Toujours préfixer avec `test_`
- Exemple: `test_locations.py`, `test_ptc_client.py`

Classes de tests:
- Format CamelCase avec préfixe `Test`
- Exemple: `TestConvertTimestamp`, `TestExtractPtcValue`

Fonctions de tests:
- Format snake_case avec préfixe `test_`
- Nom explicite qui décrit le comportement attendu
- Exemple: `test_converts_milliseconds_to_iso_format()`

## Configuration Mock vs Réel

Mode Mock (par défaut):
```bash
USE_MOCK=true pytest tests/
```
Utilise des données mockées, pas besoin de credentials PTC.

Mode Réel:
```bash
USE_MOCK=false pytest tests/integration/
```
Appelle l'API PTC réelle, nécessite les variables PTC_API_URL et PTC_API_KEY dans le .env.

## Quelques tips pour le debugging

Afficher les print() dans les tests:
```bash
pytest tests/ -v -s
```

S'arrêter au premier échec (utile quand il y a beaucoup d'erreurs):
```bash
pytest tests/ -x
```

Lancer un test spécifique (pratique pour debugger un seul test):
```bash
pytest tests/unit/test_ptc_transformer.py::TestExtractPtcValue::test_returns_none_for_null_value -v
```

Voir tous les warnings:
```bash
pytest tests/ -v -W all
```

## Bonnes pratiques

Quelques règles qu'on suit pour les tests:

1. Toujours écrire les tests unitaires en premier pour la logique pure
2. Mocker les appels externes dans les tests unitaires
3. Les tests doivent s'exécuter rapidement (< 5 secondes pour tous)
4. Chaque test doit être indépendant et pouvoir s'exécuter seul
5. Le nom du test doit être explicite et décrire ce qu'il vérifie

## Documentation technique

- Framework: pytest
- Mocking: pytest-mock
- Configuration dans pytest.ini à la racine du projet
