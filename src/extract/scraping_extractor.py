from __future__ import annotations

import logging
import re

import requests
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.common import ROOT_DIR, atomic_write_json, build_manifest, timestamp_slug, utc_now_iso


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def _download(url: str, headers: dict[str, str], timeout: int) -> str:
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def _clean_integer(value: str) -> int | None:
    cleaned = re.sub(r"[\s,\u00a0\u202f]", "", re.sub(r"\[[^]]*\]", "", value))
    return int(cleaned) if cleaned.isdecimal() else None


def _table_columns(table) -> tuple[int, int] | None:
    header = table.find("tr")
    if header is None:
        return None
    labels = [cell.get_text(" ", strip=True).lower() for cell in header.find_all(["th", "td"], recursive=False)]
    country = next((i for i, label in enumerate(labels) if "country" in label or "location" in label), None)
    population = next((i for i, label in enumerate(labels) if "population" in label), None)
    return (country, population) if country is not None and population is not None else None


def extract(settings: dict, logger: logging.Logger) -> dict:
    cfg = settings["sources"]["scraping"]
    headers = {"User-Agent": settings["project"]["user_agent"]}
    logger.info("SCRAPING | demarrage | %s", cfg["url"])
    html = _download(cfg["url"], headers, settings["project"]["timeout_seconds"])

    raw_dir = ROOT_DIR / settings["output"]["raw_directory"] / "scraping"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = timestamp_slug()
    html_path = raw_dir / f"countries_page_{stamp}.html"
    html_path.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    preferred = soup.find("table", id=cfg.get("table_id")) if cfg.get("table_id") else None
    candidates = [preferred] if preferred is not None else []
    candidates.extend(table for table in soup.select("table.wikitable") if table is not preferred)
    selected = None
    for table in candidates:
        columns = _table_columns(table)
        if columns is not None:
            selected = (table, columns)
            break
    if selected is None:
        raise ValueError("Aucun tableau avec colonnes pays et population detecte")
    table, (country_col, population_col) = selected

    records = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) <= max(country_col, population_col):
            continue
        country = re.sub(r"\[[^]]*\]", "", cells[country_col].get_text(" ", strip=True)).strip()
        if not country or country.casefold() == "world":
            continue
        population = _clean_integer(cells[population_col].get_text(" ", strip=True))
        if population is None:
            logger.warning("SCRAPING | population invalide | pays=%s", country)
            continue
        records.append(
            {
                "country_name": country,
                "population_scraped": population,
                "source_type": "scraping",
                "source_url": cfg["url"],
                "extracted_at": utc_now_iso(),
            }
        )

    if not records:
        raise ValueError("Le tableau HTML n'a produit aucun pays valide")

    output = raw_dir / f"countries_scraping_{stamp}.json"
    atomic_write_json(records, output)
    logger.info("SCRAPING | succes | lignes=%s | fichier=%s", len(records), output)
    manifest = build_manifest("scraping", output, len(records))
    manifest["html_snapshot"] = str(html_path.relative_to(ROOT_DIR))
    return manifest
