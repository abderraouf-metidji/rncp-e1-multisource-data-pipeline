import json

import responses
import pytest

from src.common import (
    ROOT_DIR,
    configure_logging,
    load_settings,
)
from src.extract.api_extractor import RESPONSE_FIELDS, extract
from src.transform.aggregate_countries import standardize_api


@responses.activate
def test_api_extraction_succeeds(monkeypatch):
    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    settings = load_settings()

    responses.get(
        settings["sources"]["api"]["url"],
        json={
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
                        "capitals": [{"name": "Paris"}],
                        "region": "Europe",
                        "subregion": "Western Europe",
                        "area": {"kilometers": 551695, "miles": 213011},
                        "population": 68000000,
                        "currencies": [{"code": "EUR", "name": "Euro"}],
                        "languages": [{"iso639_3": "fra", "name": "French"}],
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
    output = ROOT_DIR / result["output_file"]
    record = json.loads(output.read_text(encoding="utf-8"))[0]
    assert record["capital"] == "Paris"
    assert record["area_km2"] == 551695
    assert record["currencies"] == ["EUR"]
    assert record["languages"] == ["French"]
    standardized = standardize_api(output, {})
    assert standardized.loc[0, "currencies"] == "EUR"
    assert standardized.loc[0, "languages"] == "French"


@responses.activate
def test_api_extraction_reads_all_pages(monkeypatch):
    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    settings = load_settings()
    settings["sources"]["api"]["page_size"] = 1
    url = settings["sources"]["api"]["url"]
    responses.get(
        url,
        json={"data": {"objects": [{"codes": {"alpha_2": "FR"}, "names": {"common": "France"}}], "meta": {"more": True}}},
        match=[responses.matchers.query_param_matcher({"limit": "1", "offset": "0", "response_fields": RESPONSE_FIELDS})],
    )
    responses.get(
        url,
        json={"data": {"objects": [{"codes": {"alpha_2": "DE"}, "names": {"common": "Germany"}}], "meta": {"more": False}}},
        match=[responses.matchers.query_param_matcher({"limit": "1", "offset": "1", "response_fields": RESPONSE_FIELDS})],
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
