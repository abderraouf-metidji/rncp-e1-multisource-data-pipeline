# E1 — synthèse du projet et des preuves

Ce document donne un point d'entrée commun aux cinq compétences. Il regroupe les consignes utiles des PDF [Compétences](../Dépouillement%20REAC%2037827%20-%20compétences.pdf) et [Général](../Dépouillement%20REAC%2037827%20-%20Général.pdf), sans remplacer ces documents ni la grille officielle du REAC. Les deux PDF sont des commentaires pédagogiques ; seul le référentiel officiel fait foi.

## Projet présenté

- **Sujet** : un référentiel de pays enrichi d'indicateurs démographiques et économiques.
- **Objectif fonctionnel** : retrouver et consulter des pays et leurs indicateurs depuis une API.
- **Objectif technique** : collecter cinq familles de sources, vérifier et rapprocher leurs données, conserver les sorties brutes, charger un modèle relationnel, puis exposer ce modèle.
- **Environnement** : Python, PostgreSQL via Docker Compose, DuckDB/Parquet, FastAPI.
- **Contraintes** : réseau et structure des sources externes variables, clé REST Countries personnelle pour l'extraction complète, correspondance des noms pour le scraping, données d'exemple limitées à dix pays pour plusieurs sources.
- **Organisation et budget** : projet individuel de démonstration, principalement fondé sur des outils locaux et des données d'exemple. Documenter le coût réel d'une éventuelle clé API, de l'hébergement et du temps de travail avant la soutenance ; aucun montant n'est établi dans le dépôt.

## Parcours des données

```text
API REST Countries ─┐
HTML Wikipédia ─────┤
CSV ISO ────────────┼─> C1 sorties RAW ─> C3 jeu consolidé ─> C4 PostgreSQL ─> C5 API REST
PostgreSQL exemple ─┤                       │
Parquet/DuckDB ─────┘                       └─> contrôles qualité et lignage

PostgreSQL exemple + indicateurs SQL ─> C2 requêtes et exports de démonstration
```

C2 utilise actuellement `country_reference` et `country_indicators`, des tables de démonstration distinctes du modèle final de C4 (`country` et `country_indicator`). Cette séparation doit être annoncée à l'oral. Les exports C2 ne sont pas l'entrée du script C3 : C3 lit les sorties RAW de C1.

## Matrice de preuves C1 à C5

| Compétence | Ce qui existe | Preuve à préparer avant remise |
| --- | --- | --- |
| **C1** Automatiser l'extraction | Cinq extracteurs, configuration YAML, sorties RAW, manifeste, tests locaux. [Rapport C1](C1_rapport.pdf), [script oral](script_oral_c1.md). | Exécution réelle des cinq sources, réponse API avec une vraie clé, capture HTML, PostgreSQL et DuckDB, manifeste avec cinq succès. Corriger le rapport C1 avant remise. |
| **C2** Requêter en SQL | Trois requêtes métier, une requête `EXPLAIN ANALYZE`, index et lanceur Python. [Guide](C2_guide.md), [script oral](C2_script_oral.md). | Exécuter la préparation SQL et les quatre requêtes sur PostgreSQL, conserver les exports et expliquer le plan. |
| **C3** Agréger | Script de normalisation, règles de priorité, rapprochement des noms, rapport qualité et lignage. [Guide](C3_guide.md), [script oral](C3_script_oral.md). | Exécuter sans `--allow-missing` après C1 ; montrer les cinq entrées réellement utilisées et une sortie qualité `passed`. |
| **C4** Modéliser et charger | Schéma relationnel, MCD/MLD, chargement et audit prévus dans le code. [Guide](C4_guide.md), [MCD/MLD](diagrams/C4_MCD_merise.md), [script oral](C4_script_oral.md). | Charger réellement le fichier C3 dans PostgreSQL, montrer contraintes, audit et contrôles d'intégrité. Expliquer l'absence de données personnelles dans le jeu métier. |
| **C5** Mettre à disposition | FastAPI, ressources CRUD, authentification HTTP Basic, OpenAPI et tests simulés. [Guide](C5_guide.md), [script oral](C5_script_oral.md). | Exécuter l'API sur la base C4 chargée et capturer des requêtes GET/POST/PUT/DELETE, un refus 401 et Swagger. |

Le [guide des preuves](guide_preuves.md) donne les noms de captures. Les fichiers de `docs/preuves/` sont à constituer à partir d'exécutions réelles ; les tests automatisés ne suffisent pas à eux seuls.

## Points à ne pas surdéclarer

1. Le [rapport C1 PDF](C1_rapport.pdf) est un **brouillon**. Il annonce notamment des monnaies et langues extraites de l'API alors que l'extracteur C1 ne les exporte pas ; sa description de la réponse JSON doit être alignée sur `data.objects` de l'API v5. Le CSV est maintenant refusé si des codes ISO sont dupliqués, au lieu de les supprimer silencieusement. Les mentions de preuves et de résultats doivent être revérifiées après exécution.
2. La clé REST Countries `rc_live_demo` renvoie un exemple et ne permet pas l'extraction complète. La commande C1 nécessite une clé personnelle dans `.env`.
3. Les données d'entrée locales sont un petit exemple reproductible ; DuckDB et Parquet démontrent la technologie, pas un volume massif.
4. Le script C3 en mode `--allow-missing` sert au développement. Il ne prouve pas l'agrégation des cinq sources.
5. Les tests C2, C4 et C5 contrôlent principalement les contrats et structures sans PostgreSQL réel. Capturer séparément une exécution de bout en bout.
6. Pour C5, HTTP Basic convient à une démonstration locale. Dès que l'API est exposée sur un réseau, utiliser HTTPS et des identifiants non triviaux.

## Préparation de l'oral

Les PDF conseillent environ **15 minutes pour la présentation du projet et E1**, dont 2 à 3 minutes pour le contexte, puis les compétences. Prévoir une diapositive identifiable par compétence, des captures lisibles et une explication de l'ordre des traitements. Préparer aussi une justification du choix de DuckDB, de PostgreSQL, des priorités de fusion, des index SQL et du périmètre RGPD. Les durées et critères définitifs sont à vérifier dans la convocation et la grille officielle.
