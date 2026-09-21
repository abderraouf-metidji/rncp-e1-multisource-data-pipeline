# RNCP 37827 — E1 : référentiel de pays multisource

Projet de préparation à l'ensemble **E1 — collecter, stocker et mettre à disposition des données**. Le flux couvre les compétences C1 à C5 : extraction de cinq familles de sources, requêtes SQL, harmonisation, chargement PostgreSQL et API REST.

## Parcours du projet

| Compétence | Étape | Code et documentation |
| --- | --- | --- |
| C1 | Extraire API, HTML, CSV, PostgreSQL et Parquet/DuckDB | [`src/extract/`](src/extract/), [`src/main.py`](src/main.py), [rapport C1](docs/C1_rapport.pdf) |
| C2 | Requêter et exporter des résultats SQL | [`database/queries/`](database/queries/), [`src/queries/`](src/queries/), [guide C2](docs/C2_guide.md) |
| C3 | Harmoniser et consolider les sources | [`src/transform/`](src/transform/), [`config/c3_mapping.yaml`](config/c3_mapping.yaml), [guide C3](docs/C3_guide.md) |
| C4 | Modéliser et charger la base finale | [`database/c4_schema.sql`](database/c4_schema.sql), [`src/load/`](src/load/), [guide C4](docs/C4_guide.md) |
| C5 | Exposer les données par API authentifiée | [`src/api/`](src/api/), [guide C5](docs/C5_guide.md) |

Le [dossier de synthèse E1](docs/E1_synthese.md) relie les exigences des deux PDF, les livrables et les preuves encore nécessaires. Les PDF de référence sont [Compétences](Dépouillement%20REAC%2037827%20-%20compétences.pdf) et [Général](Dépouillement%20REAC%2037827%20-%20Général.pdf). Ce sont des commentaires du référentiel : la grille officielle du REAC fait foi.

## Installation

Python 3.11 ou 3.12, Docker Compose pour PostgreSQL et une clé personnelle REST Countries sont nécessaires à l'exécution complète.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Sur Linux/macOS, activer l'environnement avec `source .venv/bin/activate` et copier le fichier avec `cp .env.example .env`. Renseigner ensuite `RESTCOUNTRIES_API_KEY` et `API_PASSWORD` dans `.env`. La clé `rc_live_demo` ne fournit qu'un exemple : elle ne permet pas d'extraire tous les pays. Ne jamais committer `.env`.

L'API C5 charge `.env` au démarrage et donne priorité aux variables du processus. Sans identifiants valides et mot de passe d'au moins 12 caractères, les routes protégées refusent l'accès (voir le [guide C5](docs/C5_guide.md)).

## Exécution par étape

```powershell
docker compose up -d
python -m src.main --sources all --continue-on-error
Get-Content .\database\c2_schema_extension.sql -Raw | docker compose exec -T postgres psql -U rncp -d countries
Get-Content .\database\indexes.sql -Raw | docker compose exec -T postgres psql -U rncp -d countries
python -m src.queries.run_queries --query all
python -m src.transform.aggregate_countries
python -m src.load.load_countries --indicator-year 2024
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

La commande C2 utilise les tables d'exemple `country_reference` et `country_indicators`. Elle constitue une démonstration SQL distincte du chargement C4. Après C1, vérifier que le manifeste contient bien cinq succès avant de lancer C3. Voir les détails dans le [guide C2](docs/C2_guide.md).

Pour travailler sans réseau ni PostgreSQL :

```powershell
python -m src.main --sources file bigdata
python -m src.transform.aggregate_countries --allow-missing
```

Le mode `--allow-missing` est réservé au développement ; la preuve finale C3 exige les cinq sorties C1.

## Tests et preuves

```powershell
python -m pytest -q
```

Les tests automatisés vérifient surtout les contrats locaux et utilisent des simulations pour l'API et la base. Ils ne remplacent pas les preuves d'une exécution complète sur les services réels. Les sorties sont dans `data/raw/`, `data/processed/`, `data/quality/` et `data/query_results/`. Le [guide des preuves](docs/guide_preuves.md) et les guides C2 à C5 indiquent les captures à constituer.

Le [rapport C1](docs/C1_rapport.pdf) est encore un document de travail : certaines affirmations et captures sont à mettre à jour avant remise. Les scripts oraux sont dans `docs/`.
