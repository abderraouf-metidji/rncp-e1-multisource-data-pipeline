# Script oral C3 - 2 à 3 minutes

J'ai construit un script pandas qui harmonise les cinq sources collectées en C1. J'ai choisi pandas car les entrées sont hétérogènes : JSON, CSV et Parquet, avec des schémas différents avant chargement dans la base finale.

Le référentiel CSV ISO sert de population canonique et le code ISO3 constitue la clé de rapprochement. La source issue du scraping ne contenant pas toujours ce code, je normalise le nom du pays en supprimant accents, ponctuation, espaces parasites et références, puis j'applique une table d'alias explicite.

Chaque champ possède une priorité documentée. Par exemple, la population provient d'abord du fichier Parquet, puis du scraping et enfin de l'API. Les types sont harmonisés, les langues et monnaies sont sérialisées, et je calcule la densité ainsi que le PIB par habitant.

Le résultat contient une ligne par pays, le nombre de sources contributrices et leur liste. Un rapport qualité bloquant vérifie les identifiants obligatoires, l'unicité, les formats ISO et la cohérence des valeurs numériques. Enfin, un fichier de lignage indique précisément les fichiers RAW utilisés.
