# RNCP 37827 - C1 - Extraction multi-sources d'un referentiel de pays

## Objectif

Demontrer une extraction automatisee depuis cinq familles de sources: API Web, scraping HTML, fichier CSV, base PostgreSQL et fichier Parquet interroge avec DuckDB.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Sous Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Renseigner `RESTCOUNTRIES_API_KEY` dans `.env` avec une cle personnelle REST Countries.
La cle de demonstration `rc_live_demo` ne fournit qu'un exemple et ne permet pas
d'extraire le referentiel complet. L'extracteur utilise l'API v5 et parcourt
toutes les pages avec une taille de page de 100 au maximum.

## Demarrer PostgreSQL

```bash
docker compose up -d
```

## Executer les extractions

```bash
python -m src.main --sources all --continue-on-error
```

Executer seulement les sources locales, sans Internet ni PostgreSQL:

```bash
python -m src.main --sources file bigdata
```

## Tests

```bash
pytest -q
```

## Sorties

Les donnees brutes sont conservees dans `data/raw/<source>/`. Chaque execution genere egalement un manifeste contenant le nombre de lignes, la taille, l'empreinte SHA-256, la date UTC et l'etat de chaque extraction.

## Preuves a capturer

1. Terminal lors de l'execution des cinq sources.
2. Swagger ou documentation de REST Countries et exemple JSON.
3. Page HTML et tableau inspecte pour le scraping.
4. Fichier CSV et controles de schema.
5. Conteneur PostgreSQL actif et resultat de la requete.
6. Requete DuckDB sur le fichier Parquet.
7. Historique Git avec des commits separes.
8. Resultat `pytest` sans erreur.
