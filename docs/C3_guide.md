# C3 - Créer des règles d'agrégation multi-sources

## Objectif

Harmoniser les cinq extractions de C1 dans un jeu final unique, documenté et contrôlé. Le code ISO3 constitue la clé principale. Lorsque le scraping ne contient pas de code ISO, le rapprochement repose sur une clé de nom normalisée puis sur le référentiel ISO.

## Règles d'harmonisation

- Codes ISO en majuscules et longueurs contrôlées.
- Noms nettoyés : espaces, accents, ponctuation et références HTML supprimés.
- Alias explicites dans `config/c3_mapping.yaml`.
- Population convertie en entier nullable.
- Superficie et PIB convertis en nombres décimaux.
- Collections de langues et monnaies sérialisées avec `|`.
- Une ligne finale par code ISO3.
- Priorité des sources documentée champ par champ.
- Calcul de la densité et du PIB par habitant.
- Traçabilité des sources contributrices par ligne.

## Priorité par défaut

- Identité du pays : référentiel CSV ISO.
- Capitale, nom officiel, langues, monnaies : API.
- Région et sous-région : base PostgreSQL puis API.
- Population : Parquet Big Data, puis scraping, puis API.
- Superficie et PIB : Parquet Big Data puis API.

## Exécution

Après exécution des cinq sources de C1 :

```powershell
python -m src.transform.aggregate_countries
```

Pendant le développement, si PostgreSQL n'est pas encore disponible :

```powershell
python -m src.transform.aggregate_countries --allow-missing
```

Le mode `--allow-missing` sert uniquement aux tests intermédiaires. La preuve finale doit utiliser les cinq sources.

## Sorties

- `data/processed/countries_consolidated_*.parquet`
- `data/processed/countries_consolidated_*.csv`
- `data/quality/c3_quality_report_*.json`
- `data/quality/c3_lineage_*.json`

## Contrôles qualité bloquants

- aucune valeur manquante sur ISO2, ISO3 et nom ;
- aucune duplication ISO2 ou ISO3 ;
- longueur valide des codes ISO ;
- pas de population négative ;
- superficie strictement positive lorsqu'elle est renseignée ;
- au moins une source contributrice par ligne.

## Captures à produire

1. Exécution réussie du script.
2. Extrait des cinq fichiers RAW.
3. Configuration des priorités et alias.
4. Aperçu du jeu final consolidé.
5. Rapport qualité avec statut `passed`.
6. Fichier de lignage listant les entrées utilisées.
7. Tests pytest réussis.
