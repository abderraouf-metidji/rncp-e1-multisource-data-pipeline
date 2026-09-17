# C4 - Modéliser les données en base et respecter le RGPD

## Objectif

Charger le jeu consolidé de C3 dans PostgreSQL selon un modèle relationnel documenté avec MERISE. Le modèle impose les clés, cardinalités, contraintes d'intégrité, index et règles de suppression.

## Modèle logique

- `region(region_id, region_name)`
- `subregion(subregion_id, #region_id, subregion_name)`
- `country(country_id, #region_id, #subregion_id, iso2, iso3, ...)`
- `country_indicator(country_indicator_id, #country_id, indicator_year, ...)`
- `data_load_audit(load_id, source_file, source_sha256, status, ...)`

## Choix de modélisation

- PostgreSQL pour les contraintes relationnelles, transactions et requêtes analytiques.
- Clés techniques numériques pour les relations internes.
- Codes ISO2 et ISO3 conservés comme clés métier uniques.
- Séparation des indicateurs annuels pour éviter de répéter les attributs stables du pays.
- Chargement transactionnel et idempotent avec `ON CONFLICT DO UPDATE`.
- Audit par empreinte SHA-256, date, statut et compteurs.
- Index sur les clés étrangères, les noms et les millésimes.

## Exécution à réaliser sur l'ordinateur Docker

Après C3 :

```powershell
python -m src.load.load_countries --indicator-year 2024
```

Le script crée le schéma puis charge automatiquement le dernier fichier :

```text
data/processed/countries_consolidated_*.parquet
```

Validation :

```powershell
Get-Content .\database\c4_validation_queries.sql -Raw |
  docker compose exec -T postgres psql -U rncp -d countries
```

## RGPD

Le jeu de données porte sur des pays et des indicateurs agrégés. Il ne contient aucune donnée permettant d'identifier directement ou indirectement une personne physique. Le RGPD n'est donc pas applicable au contenu métier du projet.

Les mesures retenues restent les suivantes :

- aucun nom, courriel, adresse, identifiant utilisateur ou adresse IP dans les tables métier ;
- secrets de connexion stockés dans `.env`, exclu de Git ;
- logs limités aux statuts, chemins techniques, compteurs et messages d'erreur ;
- aucune donnée métier complète recopiée dans les logs ;
- accès PostgreSQL protégé par authentification ;
- principe de minimisation appliqué aux colonnes ;
- registre de traitement à créer si une future version introduit des données personnelles ;
- procédure future prévue pour l'information, la durée de conservation, la rectification, l'effacement et la gestion des violations.

## Captures à produire

1. MCD et MLD.
2. Création des tables dans PostgreSQL.
3. Liste des contraintes et index.
4. Exécution du chargement.
5. Dernière ligne de `data_load_audit` avec statut `success`.
6. Contrôles sans doublon ni clé orpheline.
7. Tests pytest réussis.
