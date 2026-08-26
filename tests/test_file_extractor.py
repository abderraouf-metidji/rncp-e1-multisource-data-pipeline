from src.common import configure_logging, load_settings
from src.extract.file_extractor import extract


def test_file_extraction_succeeds():
    settings = load_settings()
    logger = configure_logging(settings["output"]["log_file"])
    result = extract(settings, logger)
    assert result["status"] == "success"
    assert result["rows"] == 10
    assert result["sha256"]
