# Script oral C5 - 2 à 3 minutes

J'ai exposé le modèle relationnel C4 avec une API REST FastAPI. Les ressources région, sous-région, pays et indicateur disposent des opérations de liste, lecture par identifiant, création, mise à jour et suppression. La table d'audit est uniquement lisible afin de préserver la valeur probante des traces de chargement.

Les routes métier sont protégées par HTTP Basic. Les identifiants sont fournis par variables d'environnement et comparés de manière constante. Pydantic contrôle les formats, notamment les codes ISO, les millésimes et les valeurs numériques. SQLAlchemy paramètre les requêtes et les contraintes PostgreSQL restent la dernière barrière d'intégrité.

Swagger, ReDoc et le contrat OpenAPI sont générés automatiquement. J'ai ajouté la pagination, la recherche sur les noms, les statuts HTTP 201, 204, 401, 404, 409 et 422, ainsi qu'un endpoint de santé qui vérifie la connexion à la base.

Les tests vérifient l'authentification et la présence de toutes les routes CRUD dans OpenAPI. Dans un environnement de production, HTTP Basic serait obligatoirement placé derrière HTTPS et remplacé de préférence par OAuth2 ou OpenID Connect.
