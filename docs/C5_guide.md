# C5 - Développer une API mettant à disposition le jeu de données

## Objectif

Exposer les ressources du schéma C4 avec FastAPI, SQLAlchemy et PostgreSQL. Les routes métier sont protégées par HTTP Basic. Swagger et ReDoc sont générés automatiquement.

## Ressources

- `/regions`
- `/subregions`
- `/countries`
- `/indicators`
- `/audits`, en lecture seule car cette table constitue une trace technique
- `/health`, public pour le contrôle de disponibilité

Chaque ressource métier possède : liste paginée, lecture par identifiant, création, mise à jour complète et suppression. Les audits restent volontairement non modifiables par API afin de préserver leur intégrité.

## Installation

Installer toutes les dépendances depuis le fichier unique à la racine :

```powershell
python -m pip install -r requirements.txt
```

Si `.env` n'existe pas encore, copier le modèle sans publier les secrets :

```powershell
Copy-Item .env.example .env
```

Sous PowerShell, charger les variables pour la session. Le module C5 lit les variables du processus au démarrage ; il ne charge pas automatiquement `.env` :

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://rncp:rncp@localhost:5432/countries"
$env:API_USERNAME = "rncp"
$env:API_PASSWORD = "mot-de-passe-long-et-aleatoire"
```

## Démarrage

Après création et chargement du schéma C4 :

```powershell
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Documentation :

- Swagger : `http://127.0.0.1:8000/docs`
- ReDoc : `http://127.0.0.1:8000/redoc`
- OpenAPI : `http://127.0.0.1:8000/openapi.json`

## Exemples

```powershell
curl.exe -u "$env:API_USERNAME`:$env:API_PASSWORD" "http://127.0.0.1:8000/countries/?limit=20&offset=0&search=France"
```

```powershell
curl.exe -u "$env:API_USERNAME`:$env:API_PASSWORD" `
  -H "Content-Type: application/json" `
  -d '{"region_name":"Test Region"}' `
  "http://127.0.0.1:8000/regions/"
```

## Sécurité

- authentification obligatoire sur toutes les données ;
- comparaison constante des identifiants avec `secrets.compare_digest` ;
- secrets fournis par variables d'environnement ;
- validation Pydantic des entrées ;
- requêtes paramétrées par SQLAlchemy ;
- erreurs 404, 409 et 422 explicites ;
- pagination limitée à 500 lignes ;
- aucune clé dans Git.

HTTP Basic est suffisant pour la démonstration locale C5, à condition d'utiliser HTTPS dans un véritable environnement réseau. Pour une mise en production, OAuth2/OIDC ou des jetons courts seraient préférables.

## Tests

```powershell
pytest -q tests/test_c5_openapi.py tests/test_c5_auth.py
```

Les tests vérifient l'accès public à la santé, le refus sans authentification, l'acceptation des bons identifiants et la présence de toutes les routes CRUD dans OpenAPI.

## Captures à produire

1. Swagger affichant toutes les ressources.
2. Bouton Authorize et authentification réussie.
3. GET liste et GET par identifiant.
4. POST avec statut 201.
5. PUT avec ressource modifiée.
6. DELETE avec statut 204.
7. Requête sans authentification avec statut 401.
8. Conflit d'intégrité avec statut 409.
9. Tests pytest réussis.
10. Endpoint `/health` avec base accessible.
