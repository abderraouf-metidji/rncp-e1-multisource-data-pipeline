from pathlib import Path

import pandas as pd

from src.transform.aggregate_countries import (
    merge_sources,
    normalize_country_key,
    quality_report,
)


def test_country_name_normalization_handles_accents_and_symbols():
    aliases = {"turkiye": "turkey"}
    assert normalize_country_key("  Türkiye [1] ", aliases) == "turkey"
    assert normalize_country_key("Côte-d'Ivoire", {}) == "cote d ivoire"


def test_merge_sources_applies_priority_and_calculates_metrics():
    config = {
        "canonical_columns": [
            "iso2", "iso3", "country_name", "official_name", "capital", "region", "subregion",
            "population", "area_km2", "gdp_usd", "density_per_km2", "gdp_per_capita_usd",
            "currencies", "languages", "source_count", "sources", "processed_at"
        ],
        "source_priority": {
            "country_name": ["file", "api", "database", "bigdata", "scraping"],
            "official_name": ["api"], "capital": ["api"], "region": ["database", "api"],
            "subregion": ["database", "api"], "population": ["bigdata", "scraping", "api"],
            "area_km2": ["bigdata", "api"], "gdp_usd": ["bigdata"],
            "currencies": ["api"], "languages": ["api"]
        },
        "quality": {"mandatory_columns": ["iso2", "iso3", "country_name"], "unique_columns": ["iso2", "iso3"], "minimum_source_count": 1},
    }
    sources = {
        "file": pd.DataFrame([{"iso2": "FR", "iso3": "FRA", "country_name": "France", "country_key": "france", "source": "file"}]),
        "api": pd.DataFrame([{"iso2": "FR", "iso3": "FRA", "country_name": "France", "official_name": "French Republic", "capital": "Paris", "region": "Europe", "subregion": "Western Europe", "population": 60_000_000, "area_km2": 550_000.0, "currencies": "EUR", "languages": "French", "country_key": "france", "source": "api"}]),
        "bigdata": pd.DataFrame([{"iso3": "FRA", "country_name": "France", "population": 68_000_000, "area_km2": 551_695.0, "gdp_usd": 3_000_000_000_000.0, "country_key": "france", "source": "bigdata"}]),
    }
    result = merge_sources(sources, config)
    assert len(result) == 1
    assert result.loc[0, "population"] == 68_000_000
    assert result.loc[0, "capital"] == "Paris"
    assert result.loc[0, "source_count"] == 3
    assert round(float(result.loc[0, "density_per_km2"]), 2) == 123.26


def test_quality_report_detects_duplicates():
    frame = pd.DataFrame({
        "iso2": ["FR", "FR"], "iso3": ["FRA", "FRA"], "country_name": ["France", "France"],
        "population": pd.Series([1, 1], dtype="Int64"), "area_km2": pd.Series([1.0, 1.0], dtype="Float64"),
        "source_count": pd.Series([1, 1], dtype="Int64")
    })
    config = {"quality": {"mandatory_columns": ["iso2", "iso3", "country_name"], "unique_columns": ["iso2", "iso3"], "minimum_source_count": 1}}
    report = quality_report(frame, config, {"file": frame})
    assert report["status"] == "failed"
    assert report["checks"]["duplicates"]["iso3"] == 1
