# Script oral C2 - 2 à 3 minutes

J’utilise PostgreSQL pour interroger deux tables de démonstration alimentées avec dix pays d’exemple. Je présente trois requêtes métier et un plan d’exécution. Ces tables sont distinctes du modèle final chargé en C4.

La première requête filtre les pays actifs, les regroupe par région et applique une condition HAVING. La deuxième est la requête complexe : un CTE sélectionne l’indicateur le plus récent par pays avec ROW_NUMBER, puis une jointure sur le code ISO enrichit le référentiel. La requête calcule la densité, le PIB par habitant et un classement régional avec DENSE_RANK. La troisième requête produit des statistiques régionales et calcule un PIB par habitant pondéré.

Je n’utilise pas SELECT étoile. Les filtres sont appliqués au plus tôt et les paramètres sont liés par SQLAlchemy. J’ai créé des index sur les clés de jointure et sur la recherche du dernier millésime. Enfin, EXPLAIN ANALYZE avec BUFFERS permet de comparer le plan réel et de vérifier l’utilisation des index. Les résultats des requêtes sont exportés en CSV pour la preuve C2 ; le script C3 lit les sorties brutes de C1.
