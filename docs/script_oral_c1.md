# Script oral C1 - cible 3 minutes

J'ai construit un pipeline automatise qui collecte des informations de meme nature, les pays, depuis cinq familles de sources. Les codes ISO servent au rapprochement quand ils sont presents ; le scraping demande une correspondance par nom en C3.

La premiere source est l'API REST Countries v5. Avec une cle personnelle, le script parcourt les pages, controle le statut, applique des tentatives automatiques en cas d'erreur reseau et conserve une selection de champs en JSON.

La deuxieme source est un tableau HTML public listant les populations. Je conserve une copie de la page brute, puis BeautifulSoup repere les colonnes pays et population et lit directement le texte des cellules. Le total mondial est exclu et les populations restent des entiers exacts.

La troisieme source est un fichier CSV ISO. Le script controle l'encodage, les colonnes obligatoires, les valeurs manquantes et les doublons.

La quatrieme source est PostgreSQL, lance avec Docker Compose. La requete est parametree, limitee aux colonnes utiles et la connexion est fermee proprement.

La cinquieme source repose sur un fichier Parquet immuable interroge avec DuckDB. Le script controle le schema, projette uniquement les colonnes utiles et applique les filtres avant l'export RAW compresse.

Toutes les sorties sont horodatees. Un manifeste enregistre le nombre de lignes, la taille, l'empreinte SHA-256 et les erreurs. Le projet est versionne avec Git et teste avec pytest.
