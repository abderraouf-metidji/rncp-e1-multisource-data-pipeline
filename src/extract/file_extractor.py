from __future__ import annotations

import logging
import shutil

import pandas as pd

from src.common import ROOT_DIR, build_manifest, timestamp_slug

REQUIRED_COLUMNS = {"iso2", "iso3", "country_name"}


def validate_iso_frame(frame: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Colonnes obligatoires absentes: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Le référentiel ISO est vide")

    for column in ("iso2", "iso3", "country_name"):
        values = frame[column]
        if values.isna().any() or values.str.strip().eq("").any():
            raise ValueError(f"Valeurs obligatoires manquantes dans {column}")

    for column, length in (("iso2", 2), ("iso3", 3)):
        if not frame[column].str.fullmatch(rf"[A-Z]{{{length}}}").all():
            raise ValueError(f"Codes {column} invalides : lettres majuscules attendues")
        if frame[column].duplicated().any():
            raise ValueError(f"Codes {column} dupliqués dans le référentiel ISO")


def extract(settings: dict, logger: logging.Logger) -> dict:
    source = ROOT_DIR / settings["sources"]["file"]["path"]
    logger.info("FICHIER | demarrage | %s", source)
    if not source.exists():
        raise FileNotFoundError(f"Fichier source introuvable: {source}")

    frame = pd.read_csv(source, encoding="utf-8", dtype=str)
    validate_iso_frame(frame)

    output = ROOT_DIR / settings["output"]["raw_directory"] / "file" / f"countries_iso_{timestamp_slug()}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
    logger.info("FICHIER | succes | lignes=%s | fichier=%s", len(frame), output)
    return build_manifest("file", output, len(frame))
