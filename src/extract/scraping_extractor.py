from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.common import ROOT_DIR, atomic_write_json, build_manifest, timestamp_slug, utc_now_iso
from io import StringIO


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
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


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
    table = soup.find("table", id=cfg.get("table_id")) or soup.find("table", class_="wikitable")
    if table is None:
        raise ValueError("Aucun tableau de population detecte dans la page HTML")

    frames = pd.read_html(StringIO(str(table)))
    if not frames:
        raise ValueError("Le tableau HTML n'a produit aucune donnee")
    frame = frames[0]
    frame.columns = [str(col).lower().replace(" ", "_") for col in frame.columns]

    country_col = next((c for c in frame.columns if "country" in c or "location" in c), None)
    population_col = next((c for c in frame.columns if "population" in c), None)
    if country_col is None or population_col is None:
        raise ValueError(f"Colonnes attendues absentes: {list(frame.columns)}")

    records = []
    for _, row in frame.iterrows():
        country = re.sub(r"\[[^]]*\]", "", str(row[country_col])).strip()
        if not country or country.lower() == "nan":
            continue
        records.append(
            {
                "country_name": country,
                "population_scraped": _clean_integer(row[population_col]),
                "source_type": "scraping",
                "source_url": cfg["url"],
                "extracted_at": utc_now_iso(),
            }
        )

    output = raw_dir / f"countries_scraping_{stamp}.json"
    atomic_write_json(records, output)
    logger.info("SCRAPING | succes | lignes=%s | fichier=%s", len(records), output)
    manifest = build_manifest("scraping", output, len(records))
    manifest["html_snapshot"] = str(html_path.relative_to(ROOT_DIR))
    return manifest
