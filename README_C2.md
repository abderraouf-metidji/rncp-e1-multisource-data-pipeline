# Ajout C2 au dépôt E1

Copier le contenu de ce dossier à la racine du dépôt `rncp-e1-multisource-data-pipeline`, en fusionnant les dossiers existants.

Commandes principales :

```powershell
pytest -q
python -m src.queries.run_queries --query all
```

Ne pas lancer la partie PostgreSQL tant que Docker ou un serveur PostgreSQL équivalent n’est pas disponible. Les tests statiques SQL peuvent fonctionner sans base.
