# MCD - Modèle conceptuel des données

```mermaid
erDiagram
    REGION ||--o{ SUBREGION : contient
    REGION ||--o{ COUNTRY : classe
    SUBREGION ||--o{ COUNTRY : précise
    COUNTRY ||--o{ COUNTRY_INDICATOR : possède

    REGION {
        bigint region_id PK
        varchar region_name UK
    }
    SUBREGION {
        bigint subregion_id PK
        bigint region_id FK
        varchar subregion_name
    }
    COUNTRY {
        bigint country_id PK
        bigint region_id FK
        bigint subregion_id FK
        char iso2 UK
        char iso3 UK
        varchar country_name
        varchar official_name
        varchar capital
    }
    COUNTRY_INDICATOR {
        bigint country_indicator_id PK
        bigint country_id FK
        integer indicator_year
        bigint population
        numeric area_km2
        numeric gdp_usd
    }
```

## Cardinalités

- Une région contient zéro à plusieurs sous-régions.
- Une sous-région appartient à une et une seule région.
- Un pays peut être rattaché à une région et à une sous-région.
- Un pays possède zéro à plusieurs jeux d'indicateurs annuels.
- Un jeu d'indicateurs appartient à un seul pays.
