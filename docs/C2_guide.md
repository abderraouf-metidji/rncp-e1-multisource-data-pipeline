# C2 - Requêter des données en SQL

## Objectif

Démontrer plusieurs requêtes SQL réellement utilisées, dont une requête complexe avec filtre, conditions, jointure, agrégation et fonctions de fenêtre. Documenter également les choix de performance avec des index et `EXPLAIN ANALYZE`.

## Préparation de la base

Après le démarrage de PostgreSQL, dans PowerShell :

```powershell
Get-Content .\database\c2_schema_extension.sql -Raw |
  docker compose exec -T postgres psql -U rncp -d countries

Get-Content .\database\indexes.sql -Raw |
  docker compose exec -T postgres psql -U rncp -d countries
```

## Exécution

```powershell
python -m src.queries.run_queries --query all
```

Exécutions unitaires :

```powershell
python -m src.queries.run_queries --query regions
python -m src.queries.run_queries --query indicators
python -m src.queries.run_queries --query statistics
python -m src.queries.run_queries --query explain
```

## Preuves à capturer

1. Résultat de la requête simple avec filtre et agrégation.
2. Résultat de la jointure complexe.
3. Résultat des statistiques par région.
4. Plan `EXPLAIN ANALYZE`.
5. Liste des index avec `\di`.
6. Exports CSV réellement générés.
7. Tests `pytest -q` réussis.

## Positionnement dans le rapport

- Requête 1 : maîtrise du filtrage, du regroupement et de `HAVING`.
- Requête 2 : maîtrise des CTE, jointures, calculs conditionnels et fonctions de fenêtre.
- Requête 3 : maîtrise des agrégations et du ratio pondéré.
- Requête 4 : analyse du coût réel, des buffers et du plan d’exécution.
