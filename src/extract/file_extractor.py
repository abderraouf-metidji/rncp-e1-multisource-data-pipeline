from __future__ import annotations

import logging
import shutil

import pandas as pd

from src.common import ROOT_DIR, build_manifest, timestamp_slug

REQUIRED_COLUMNS = {"iso2", "iso3", "country_name"}


def extract(settings: dict, logger: logging.Logger) -> dict:
    source = ROOT_DIR / settings["sources"]["file"]["path"]
    logger.info("FICHIER | demarrage | %s", source)
    if not source.exists():
        raise FileNotFoundError(f"Fichier source introuvable: {source}")

    frame = pd.read_csv(source, encoding="utf-8", dtype=str)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Colonnes obligatoires absentes: {sorted(missing)}")
    frame = frame.drop_duplicates(subset=["iso2", "iso3"]).copy()
    if frame[["iso2", "iso3", "country_name"]].isna().any().any():
        raise ValueError("Le referentiel ISO contient des valeurs obligatoires manquantes")

    output = ROOT_DIR / settings["output"]["raw_directory"] / "file" / f"countries_iso_{timestamp_slug()}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False, encoding="utf-8")
    logger.info("FICHIER | succes | lignes=%s | fichier=%s", len(frame), output)
    return build_manifest("file", output, len(frame))
