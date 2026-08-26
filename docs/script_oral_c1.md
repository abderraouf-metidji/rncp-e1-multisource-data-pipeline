# Script oral C1 - cible 3 minutes

J'ai construit un pipeline automatise qui collecte des informations de meme nature, les pays, depuis cinq familles de sources. La cle commune est le code ISO.

La premiere source est l'API REST Countries. Le script realise un appel HTTP, controle le statut, applique des tentatives automatiques en cas d'erreur reseau et conserve la reponse normalisee en JSON.

La deuxieme source est un tableau HTML public listant les populations. Je conserve une copie de la page brute, puis BeautifulSoup localise le tableau et pandas transforme les lignes HTML en donnees structurees.

La troisieme source est un fichier CSV ISO. Le script controle l'encodage, les colonnes obligatoires, les valeurs manquantes et les doublons.

La quatrieme source est PostgreSQL, lance avec Docker Compose. La requete est parametree, limitee aux colonnes utiles et la connexion est fermee proprement.

La cinquieme source repose sur un fichier Parquet interroge avec DuckDB. La requete projette uniquement les colonnes utiles et applique les filtres avant l'export.

Toutes les sorties sont horodatees. Un manifeste enregistre le nombre de lignes, la taille, l'empreinte SHA-256 et les erreurs. Le projet est versionne avec Git et teste avec pytest.
