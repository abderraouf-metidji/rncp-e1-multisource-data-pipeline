-- Index proposes pour les jointures, filtres et recherche de la derniere annee
CREATE UNIQUE INDEX IF NOT EXISTS ux_country_reference_iso3
    ON country_reference (iso3);

CREATE INDEX IF NOT EXISTS ix_country_reference_active_region
    ON country_reference (active, region_name)
    WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS ix_country_indicators_iso3_year_desc
    ON country_indicators (iso3, year DESC)
    INCLUDE (population, area_km2, gdp_usd);

ANALYZE country_reference;
ANALYZE country_indicators;
