# Ajout C4 au dépôt E1

Fusionner le contenu du dossier avec la racine du dépôt E1.

Tests sans PostgreSQL :

```powershell
pytest -q
```

Exécution finale avec PostgreSQL :

```powershell
python -m src.load.load_countries --indicator-year 2024
```

La preuve finale nécessite PostgreSQL, le chargement réel du fichier C3 et les requêtes de validation.
