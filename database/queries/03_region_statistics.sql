-- C2 - Requete 3 : statistiques agregees par region
SELECT
    cr.region_name,
    COUNT(*) AS country_count,
    SUM(ci.population) AS total_population,
    ROUND(AVG(ci.population)::NUMERIC, 0) AS average_population,
    SUM(ci.gdp_usd) AS total_gdp_usd,
    ROUND(
        SUM(ci.gdp_usd)::NUMERIC / NULLIF(SUM(ci.population), 0)::NUMERIC,
        2
    ) AS weighted_gdp_per_capita_usd
FROM country_reference AS cr
INNER JOIN country_indicators AS ci
    ON ci.iso3 = cr.iso3
WHERE cr.active = TRUE
  AND ci.year = :indicator_year
GROUP BY cr.region_name
HAVING SUM(ci.population) >= :minimum_total_population
ORDER BY total_population DESC;
