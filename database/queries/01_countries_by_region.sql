-- C2 - Requete 1 : filtre, agregation et tri
SELECT
    region_name,
    COUNT(*) AS country_count
FROM country_reference
WHERE active = TRUE
  AND region_name IS NOT NULL
GROUP BY region_name
HAVING COUNT(*) >= :minimum_country_count
ORDER BY country_count DESC, region_name;
