import responses

from src.common import (
    configure_logging,
    load_settings,
)
from src.extract.api_extractor import extract


@responses.activate
def test_api_extraction_succeeds():
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