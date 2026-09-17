-- Contrôles structurels et fonctionnels après chargement

-- 1. Nombre de pays et unicité des codes
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT iso2) AS distinct_iso2,
    COUNT(DISTINCT iso3) AS distinct_iso3
FROM country;

-- 2. Recherche des clés étrangères orphelines
SELECT c.iso3, c.region_id
FROM country AS c
LEFT JOIN region AS r ON r.region_id = c.region_id
WHERE c.region_id IS NOT NULL
  AND r.region_id IS NULL;

SELECT c.iso3, c.subregion_id
FROM country AS c
LEFT JOIN subregion AS s ON s.subregion_id = c.subregion_id
WHERE c.subregion_id IS NOT NULL
  AND s.subregion_id IS NULL;

-- 3. Recherche des indicateurs orphelins
SELECT ci.country_indicator_id, ci.country_id
FROM country_indicator AS ci
LEFT JOIN country AS c ON c.country_id = ci.country_id
WHERE c.country_id IS NULL;

-- 4. Contrôle des valeurs métiers
SELECT *
FROM country_indicator
WHERE population < 0
   OR area_km2 <= 0
   OR gdp_usd < 0
   OR indicator_year NOT BETWEEN 1900 AND 2100;

-- 5. Dernier audit de chargement
SELECT *
FROM data_load_audit
ORDER BY started_at DESC
LIMIT 1;
