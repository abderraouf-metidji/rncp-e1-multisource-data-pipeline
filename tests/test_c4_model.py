from pathlib import Path

import pandas as pd
import pytest

from src.load.load_countries import validate_frame

ROOT = Path(__file__).resolve().parents[1]


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame([{
        "iso2": "FR", "iso3": "FRA", "country_name": "France",
        "source_count": 3, "sources": "file|api|bigdata",
        "processed_at": "2026-08-26T08:00:00+00:00"
    }])


def test_schema_contains_primary_foreign_and_unique_keys():
    sql = (ROOT / "database" / "c4_schema.sql").read_text(encoding="utf-8").upper()
    for keyword in ["PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK"]:
        assert keyword in sql
    loader = (ROOT / "src" / "load" / "load_countries.py").read_text(encoding="utf-8").upper()
    assert "ON CONFLICT" in loader
    for table in ["REGION", "SUBREGION", "COUNTRY", "COUNTRY_INDICATOR", "DATA_LOAD_AUDIT"]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_valid_frame_is_accepted():
    validate_frame(valid_frame())


def test_duplicate_iso_is_rejected():
    frame = pd.concat([valid_frame(), valid_frame()], ignore_index=True)
    with pytest.raises(ValueError, match="dupliqués"):
        validate_frame(frame)


def test_invalid_iso_is_rejected():
    frame = valid_frame()
    frame.loc[0, "iso3"] = "FR"
    with pytest.raises(ValueError, match="ISO3"):
        validate_frame(frame)
