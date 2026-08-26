# Ajout C3 au dépôt E1

Fusionner le contenu de ce dossier avec la racine du dépôt E1.

Tests :

```powershell
pytest -q
```

Exécution intermédiaire sans toutes les sources :

```powershell
python -m src.transform.aggregate_countries --allow-missing
```

Exécution finale obligatoire avec les cinq sources :

```powershell
python -m src.transform.aggregate_countries
```
