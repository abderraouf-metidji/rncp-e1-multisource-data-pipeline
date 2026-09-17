-- C2 - Requete 2 : jointure, conditions, calculs et fonction fenetree
WITH latest_indicators AS (
    SELECT
        ci.iso3,
        ci.country_name,
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
      AND ci.area_km2 IS NOT NULL
      AND ci.area_km2 > 0
),
enriched AS (
    SELECT
        cr.iso2,
        cr.iso3,
        cr.country_name,
        cr.region_name,
        cr.subregion_name,
        li.year,
        li.population,
        li.area_km2,
        li.gdp_usd,
        ROUND((li.population::NUMERIC / li.area_km2::NUMERIC), 2) AS density_per_km2,
        CASE
            WHEN li.gdp_usd IS NULL OR li.population = 0 THEN NULL
            ELSE ROUND((li.gdp_usd::NUMERIC / li.population::NUMERIC), 2)
        END AS gdp_per_capita_usd
    FROM country_reference AS cr
    INNER JOIN latest_indicators AS li
        ON li.iso3 = cr.iso3
       AND li.row_num = 1
    WHERE cr.active = TRUE
)
SELECT
    iso2,
    iso3,
    country_name,
    region_name,
    subregion_name,
    year,
    population,
    area_km2,
    gdp_usd,
    density_per_km2,
    gdp_per_capita_usd,
    DENSE_RANK() OVER (
        PARTITION BY region_name
        ORDER BY population DESC
    ) AS population_rank_in_region
FROM enriched
WHERE population >= :minimum_population
ORDER BY region_name, population_rank_in_region, country_name;
