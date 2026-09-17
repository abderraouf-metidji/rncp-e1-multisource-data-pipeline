CREATE TABLE IF NOT EXISTS country_indicators (
    iso3 CHAR(3) NOT NULL,
    country_name VARCHAR(150) NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1900 AND 2100),
    population BIGINT CHECK (population >= 0),
    area_km2 NUMERIC(14, 2) CHECK (area_km2 > 0),
    gdp_usd NUMERIC(22, 2) CHECK (gdp_usd >= 0),
    PRIMARY KEY (iso3, year),
    CONSTRAINT fk_country_indicators_country
        FOREIGN KEY (iso3) REFERENCES country_reference (iso3)
);

INSERT INTO country_indicators (iso3, country_name, year, population, area_km2, gdp_usd)
VALUES
('FRA','France',2024,68551653,551695,3050000000000),
('DEU','Germany',2024,83577140,357022,4650000000000),
('ESP','Spain',2024,48619695,505990,1720000000000),
('ITA','Italy',2024,58989749,301340,2370000000000),
('PRT','Portugal',2024,10639726,92212,301000000000),
('BEL','Belgium',2024,11787423,30528,655000000000),
('NLD','Netherlands',2024,17942642,41850,1150000000000),
('LUX','Luxembourg',2024,672050,2586,91000000000),
('CHE','Switzerland',2024,8961600,41285,938000000000),
('AUT','Austria',2024,9159993,83879,521000000000)
ON CONFLICT (iso3, year) DO UPDATE SET
    country_name = EXCLUDED.country_name,
    population = EXCLUDED.population,
    area_km2 = EXCLUDED.area_km2,
    gdp_usd = EXCLUDED.gdp_usd;
