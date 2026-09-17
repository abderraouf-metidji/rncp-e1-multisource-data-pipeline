# Script oral C4 - 2 à 3 minutes

J'ai modélisé les données avec une approche MERISE. Le pays est l'entité centrale. Une région contient plusieurs sous-régions, une sous-région peut regrouper plusieurs pays et un pays possède plusieurs millésimes d'indicateurs.

Dans le modèle logique, j'utilise des clés techniques pour les relations internes et je conserve ISO2 et ISO3 comme clés métier uniques. Les indicateurs sont séparés du référentiel pays afin d'éviter la répétition des attributs stables lorsqu'un nouveau millésime est chargé.

PostgreSQL garantit l'intégrité avec des clés primaires, étrangères, contraintes d'unicité et contrôles de domaine. Le chargement est transactionnel et idempotent grâce aux upserts. Une table d'audit conserve l'empreinte SHA-256 du fichier, les dates, le statut et les compteurs.

Concernant le RGPD, le contenu métier ne contient aucune donnée personnelle puisqu'il décrit uniquement des pays et des indicateurs agrégés. J'applique néanmoins la minimisation, l'exclusion des secrets de Git, l'authentification à la base et des logs sans contenu personnel. Si des données personnelles étaient ajoutées, un registre de traitement et les procédures d'exercice des droits seraient nécessaires.
