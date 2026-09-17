import responses
import pytest

from src.common import (
    configure_logging,
    load_settings,
)
from src.extract.api_extractor import extract


@responses.activate
def test_api_extraction_succeeds(monkeypatch):
    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    settings = load_settings()

    responses.get(
        settings["sources"]["api"]["url"],
        json={
            "success": True,
            "data": {
                "objects": [
                    {
                        "codes": {
                            "alpha_2": "FR",
                            "alpha_3": "FRA",
                        },
                        "names": {
                            "common": "France",
                            "official": "French Republic",
                        },
                        "capital": ["Paris"],
                        "geography": {
                            "region": "Europe",
                            "subregion": "Western Europe",
                            "area": 551695,
                        },
                        "demographics": {
                            "population": 68000000,
                        },
                    }
                ],
                "meta": {
                    "count": 1,
                    "more": False,
                },
            },
        },
        status=200,
        content_type="application/json",
    )

    logger = configure_logging(
        settings["output"]["log_file"]
    )

    result = extract(
        settings,
        logger,
    )

    assert result["rows"] == 1
    assert result["status"] == "success"


@responses.activate
def test_api_extraction_reads_all_pages(monkeypatch):
    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    settings = load_settings()
    settings["sources"]["api"]["page_size"] = 1
    url = settings["sources"]["api"]["url"]
    responses.get(
        url,
        json={"data": {"objects": [{"codes": {"alpha_2": "FR"}, "names": {"common": "France"}}], "meta": {"more": True}}},
        match=[responses.matchers.query_param_matcher({"limit": "1", "offset": "0"})],
    )
    responses.get(
        url,
        json={"data": {"objects": [{"codes": {"alpha_2": "DE"}, "names": {"common": "Germany"}}], "meta": {"more": False}}},
        match=[responses.matchers.query_param_matcher({"limit": "1", "offset": "1"})],
    )

    result = extract(settings, configure_logging(settings["output"]["log_file"]))

    assert result["rows"] == 2
    assert len(responses.calls) == 2
    assert responses.calls[0].request.headers["Authorization"] == "Bearer test_key"


def test_api_extraction_rejects_demo_key(monkeypatch):
    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "rc_live_demo")
    settings = load_settings()
    with pytest.raises(ValueError, match="vraie cle API"):
        extract(settings, configure_logging(settings["output"]["log_file"]))
