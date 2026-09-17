BEGIN;

CREATE TABLE IF NOT EXISTS region (
    region_id BIGSERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subregion (
    subregion_id BIGSERIAL PRIMARY KEY,
    region_id BIGINT NOT NULL,
    subregion_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subregion_region
        FOREIGN KEY (region_id)
        REFERENCES region (region_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT uq_subregion_region_name
        UNIQUE (region_id, subregion_name)
);

CREATE TABLE IF NOT EXISTS country (
    country_id BIGSERIAL PRIMARY KEY,
    region_id BIGINT,
    subregion_id BIGINT,
    iso2 CHAR(2) NOT NULL,
    iso3 CHAR(3) NOT NULL,
    country_name VARCHAR(150) NOT NULL,
    official_name VARCHAR(200),
    capital VARCHAR(150),
    currencies TEXT,
    languages TEXT,
    source_count SMALLINT NOT NULL DEFAULT 1 CHECK (source_count >= 1),
    sources TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_country_iso2 UNIQUE (iso2),
    CONSTRAINT uq_country_iso3 UNIQUE (iso3),
    CONSTRAINT ck_country_iso2 CHECK (iso2 ~ '^[A-Z]{2}$'),
    CONSTRAINT ck_country_iso3 CHECK (iso3 ~ '^[A-Z]{3}$'),
    CONSTRAINT fk_country_region
        FOREIGN KEY (region_id)
        REFERENCES region (region_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_country_subregion
        FOREIGN KEY (subregion_id)
        REFERENCES subregion (subregion_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS country_indicator (
    country_indicator_id BIGSERIAL PRIMARY KEY,
    country_id BIGINT NOT NULL,
    indicator_year INTEGER NOT NULL,
    population BIGINT CHECK (population >= 0),
    area_km2 NUMERIC(14, 2) CHECK (area_km2 > 0),
    gdp_usd NUMERIC(22, 2) CHECK (gdp_usd >= 0),
    density_per_km2 NUMERIC(14, 2) CHECK (density_per_km2 >= 0),
    gdp_per_capita_usd NUMERIC(18, 2) CHECK (gdp_per_capita_usd >= 0),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_country_indicator_country
        FOREIGN KEY (country_id)
        REFERENCES country (country_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT uq_country_indicator_year
        UNIQUE (country_id, indicator_year),
    CONSTRAINT ck_indicator_year
        CHECK (indicator_year BETWEEN 1900 AND 2100)
);

CREATE TABLE IF NOT EXISTS data_load_audit (
    load_id UUID PRIMARY KEY,
    source_file VARCHAR(500) NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'success', 'failed')),
    rows_read INTEGER NOT NULL DEFAULT 0 CHECK (rows_read >= 0),
    countries_inserted INTEGER NOT NULL DEFAULT 0 CHECK (countries_inserted >= 0),
    countries_updated INTEGER NOT NULL DEFAULT 0 CHECK (countries_updated >= 0),
    indicators_upserted INTEGER NOT NULL DEFAULT 0 CHECK (indicators_upserted >= 0),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_country_region_id ON country (region_id);
CREATE INDEX IF NOT EXISTS ix_country_subregion_id ON country (subregion_id);
CREATE INDEX IF NOT EXISTS ix_country_name ON country (country_name);
CREATE INDEX IF NOT EXISTS ix_country_indicator_country_year
    ON country_indicator (country_id, indicator_year DESC);
CREATE INDEX IF NOT EXISTS ix_data_load_audit_started_at
    ON data_load_audit (started_at DESC);

COMMENT ON TABLE country IS 'Référentiel consolidé des pays, sans données personnelles.';
COMMENT ON TABLE country_indicator IS 'Indicateurs statistiques annuels associés à un pays.';
COMMENT ON TABLE data_load_audit IS 'Traçabilité technique des chargements, sans journaliser le contenu métier.';

COMMIT;
