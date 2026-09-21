import json

from src.common import ROOT_DIR, configure_logging, load_settings
from src.extract import scraping_extractor


def test_scraping_keeps_exact_population_and_skips_world(monkeypatch):
    html = """
    <table class="wikitable">
      <tr><th>Location</th><th>Population</th><th>Date</th></tr>
      <tr><td>World</td><td>8,232,000,000</td><td>2025</td></tr>
      <tr><td>India</td><td>1,429,404,000</td><td>2026</td></tr>
      <tr><td>France [1]</td><td>68,551,653</td><td>2024</td></tr>
    </table>
    """
    monkeypatch.setattr(scraping_extractor, "_download", lambda url, headers, timeout: html)
    settings = load_settings()

    result = scraping_extractor.extract(
        settings, configure_logging(settings["output"]["log_file"])
    )

    rows = json.loads((ROOT_DIR / result["output_file"]).read_text(encoding="utf-8"))
    assert result["rows"] == 2
    assert [(row["country_name"], row["population_scraped"]) for row in rows] == [
        ("India", 1_429_404_000),
        ("France", 68_551_653),
    ]
