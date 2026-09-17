import logging

import pytest

from src.common import ROOT_DIR, configure_logging, load_settings, sha256_file
from src.extract.file_extractor import extract


def test_file_extraction_succeeds():
    settings = load_settings()
    logger = configure_logging(settings["output"]["log_file"])
    result = extract(settings, logger)
    assert result["status"] == "success"
    assert result["rows"] == 10
    source = ROOT_DIR / settings["sources"]["file"]["path"]
    assert result["sha256"] == sha256_file(source)


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (["FR,FRA,France", "FR,FRA,France"], "iso2 dupliqués"),
        (["FR,FRA,France", "DE,FRA,Germany"], "iso3 dupliqués"),
        (["FR,FRA,France", "DE,DEU,"], "country_name"),
        (["Fr,FRA,France"], "iso2 invalides"),
    ],
)
def test_file_extraction_rejects_invalid_reference(tmp_path, rows, message):
    source = tmp_path / "countries.csv"
    source.write_text("iso2,iso3,country_name\n" + "\n".join(rows) + "\n", encoding="utf-8")
    settings = load_settings()
    settings["sources"]["file"]["path"] = str(source)

    with pytest.raises(ValueError, match=message):
        extract(settings, logging.getLogger("test_file_extractor"))
