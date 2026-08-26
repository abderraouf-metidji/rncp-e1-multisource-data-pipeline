-- C2 - Analyse du plan d'execution de la requete complexe
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
WITH latest_indicators AS (
    SELECT
        ci.iso3,
        ci.year,
        ci.population,
        ci.area_km2,
        ci.gdp_usd,
        ROW_NUMBER() OVER (
            PARTITION BY ci.iso3
            ORDER BY ci.year DESC
        ) AS row_num
    FROM country_indicators AS ci
    WHERE ci.population IS NOT NULL
      AND ci.area_km2 > 0
)
SELECT
    cr.iso3,
    cr.country_name,
    cr.region_name,
    li.year,
    li.population,
    ROUND((li.population::NUMERIC / li.area_km2::NUMERIC), 2) AS density_per_km2
FROM country_reference AS cr
INNER JOIN latest_indicators AS li
    ON li.iso3 = cr.iso3
   AND li.row_num = 1
WHERE cr.active = TRUE
  AND li.population >= 1000000
ORDER BY cr.region_name, li.population DESC;
