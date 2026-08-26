from src.common import configure_logging, load_settings
from src.extract.bigdata_extractor import extract


def test_bigdata_extraction_succeeds():
    settings = load_settings()
    logger = configure_logging(settings["output"]["log_file"])
    result = extract(settings, logger)
    assert result["status"] == "success"
    assert result["rows"] == 10
    assert result["source_parquet"].endswith(".parquet")
