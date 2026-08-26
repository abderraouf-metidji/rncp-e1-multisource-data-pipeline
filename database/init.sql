CREATE TABLE IF NOT EXISTS country_reference (
    iso2 CHAR(2) PRIMARY KEY,
    iso3 CHAR(3) UNIQUE NOT NULL,
    country_name VARCHAR(150) NOT NULL,
    region_name VARCHAR(100),
    subregion_name VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO country_reference (iso2, iso3, country_name, region_name, subregion_name)
VALUES
('FR','FRA','France','Europe','Western Europe'),
('DE','DEU','Germany','Europe','Western Europe'),
('ES','ESP','Spain','Europe','Southern Europe'),
('IT','ITA','Italy','Europe','Southern Europe'),
('PT','PRT','Portugal','Europe','Southern Europe'),
('BE','BEL','Belgium','Europe','Western Europe'),
('NL','NLD','Netherlands','Europe','Western Europe'),
('LU','LUX','Luxembourg','Europe','Western Europe'),
('CH','CHE','Switzerland','Europe','Western Europe'),
('AT','AUT','Austria','Europe','Western Europe')
ON CONFLICT (iso2) DO UPDATE SET
country_name = EXCLUDED.country_name,
region_name = EXCLUDED.region_name,
subregion_name = EXCLUDED.subregion_name,
active = TRUE;
