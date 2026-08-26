# Ajout C5 au dépôt E1

Fusionner ce dossier avec la racine du dépôt E1.

```powershell
pip install -r requirements_c5.txt
pytest -q tests/test_c5_openapi.py tests/test_c5_auth.py
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

La preuve finale nécessite le schéma C4 chargé dans PostgreSQL et une démonstration CRUD via Swagger.
