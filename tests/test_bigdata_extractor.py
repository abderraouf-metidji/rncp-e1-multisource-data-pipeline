import logging
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.common import configure_logging, load_settings
from src.extract.bigdata_extractor import extract, validate_source


def test_bigdata_extraction_succeeds():
    settings = load_settings()
    source = settings["sources"]["bigdata"]["parquet_path"]
    source_path = Path(source)
    source_mtime = source_path.stat().st_mtime_ns
    logger = configure_logging(settings["output"]["log_file"])
    result = extract(settings, logger)
    assert result["status"] == "success"
    assert result["rows"] == 10
    assert result["source_parquet"].endswith(".parquet")
    assert source_path.stat().st_mtime_ns == source_mtime


def test_bigdata_rejects_invalid_limit():
    settings = load_settings()
    settings["sources"]["bigdata"]["limit"] = 0
    with pytest.raises(ValueError, match="strictement positive"):
        extract(settings, logging.getLogger("test_bigdata"))


def test_bigdata_rejects_missing_columns(tmp_path):
    source = tmp_path / "invalid.parquet"
    connection = duckdb.connect(database=":memory:")
    try:
        pd.DataFrame({"iso3": ["FRA"]}).to_parquet(source, index=False)
        with pytest.raises(ValueError, match="Colonnes Parquet obligatoires absentes"):
            validate_source(connection, str(source))
    finally:
        connection.close()
