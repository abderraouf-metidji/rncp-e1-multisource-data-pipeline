from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml

from src.common import sha256_file

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
QUALITY_DIR = ROOT_DIR / "data" / "quality"
CONFIG_PATH = ROOT_DIR / "config" / "c3_mapping.yaml"


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("c3_aggregation")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        logger.addHandler(handler)
    return logger


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def latest_file(directory: Path, patterns: Iterable[str], required: bool = True) -> Path | None:
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(directory.glob(pattern))
    candidates = [path for path in candidates if path.is_file()]
    if not candidates:
        if required:
            raise FileNotFoundError(f"Aucun fichier trouve dans {directory} pour {list(patterns)}")
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def manifest_outputs(manifest_path: Path, source_names: set[str]) -> dict[str, Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("errors") or not isinstance(manifest.get("results"), list):
        raise ValueError(f"Exécution C1 incomplète : {manifest_path}")

    results = manifest["results"]
    if len(results) != len(source_names):
        raise ValueError(f"Le manifeste C1 ne contient pas les cinq sources : {manifest_path}")

    selected: dict[str, Path] = {}
    for entry in results:
        if not isinstance(entry, dict):
            raise ValueError(f"Entrée invalide dans le manifeste C1 : {manifest_path}")
        source = entry.get("source")
        if not isinstance(source, str) or source not in source_names or source in selected or entry.get("status") != "success":
            raise ValueError(f"Source absente, dupliquée ou en échec dans {manifest_path}")
        if not isinstance(entry.get("output_file"), str):
            raise ValueError(f"Chemin de sortie absent pour {source}")
        path = (ROOT_DIR / entry["output_file"]).resolve()
        if not path.is_relative_to((RAW_DIR / source).resolve()) or not path.is_file():
            raise ValueError(f"Sortie RAW absente ou hors du dossier de {source}: {path}")
        if path.stat().st_size != entry.get("bytes") or sha256_file(path) != entry.get("sha256"):
            raise ValueError(f"Sortie RAW modifiée depuis le manifeste C1 : {path}")
        if not isinstance(entry.get("rows"), int) or entry["rows"] < 1:
            raise ValueError(f"Sortie RAW vide pour {source}")
        selected[source] = path

    if set(selected) != source_names:
        raise ValueError(f"Le manifeste C1 ne contient pas les cinq sources : {manifest_path}")
    return selected


def normalize_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"\[[^]]*\]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip() or None


def normalize_country_key(value: Any, aliases: dict[str, str]) -> str | None:
    key = normalize_text(value)
    return aliases.get(key, key) if key else None


def clean_code(value: Any, length: int) -> str | None:
    if value is None or pd.isna(value):
        return None
    code = re.sub(r"[^A-Za-z]", "", str(value)).upper()
    return code if len(code) == length else None


def to_nullable_integer(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.replace(r"[^0-9-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce").round().astype("Int64")


def to_nullable_float(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.replace(" ", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(cleaned, errors="coerce").astype("Float64")


def serialize_collection(value: Any) -> str | None:
    if value is None or (not isinstance(value, (list, dict, tuple, set)) and pd.isna(value)):
        return None
    if isinstance(value, dict):
        value = sorted(value.keys())
    if isinstance(value, (list, tuple, set)):
        values = sorted({str(item).strip() for item in value if str(item).strip()})
        return "|".join(values) if values else None
    text = str(value).strip()
    return text or None


def standardize_file(path: Path, aliases: dict[str, str]) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype="string", encoding="utf-8")
    required = {"iso2", "iso3", "country_name"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Source file: colonnes absentes {sorted(missing)}")
    result = frame[["iso2", "iso3", "country_name"]].copy()
    result["iso2"] = result["iso2"].map(lambda value: clean_code(value, 2))
    result["iso3"] = result["iso3"].map(lambda value: clean_code(value, 3))
    result["country_key"] = result["country_name"].map(lambda value: normalize_country_key(value, aliases))
    result["source"] = "file"
    return result.drop_duplicates(subset=["iso3"], keep="last")


def standardize_api(path: Path, aliases: dict[str, str]) -> pd.DataFrame:
    frame = pd.read_json(path, encoding="utf-8")
    rename = {"region_name": "region", "subregion_name": "subregion"}
    frame = frame.rename(columns=rename)
    expected = ["iso2", "iso3", "country_name", "official_name", "capital", "region", "subregion", "population", "area_km2", "currencies", "languages"]
    result = frame.reindex(columns=expected).copy()
    result["iso2"] = result["iso2"].map(lambda value: clean_code(value, 2))
    result["iso3"] = result["iso3"].map(lambda value: clean_code(value, 3))
    result["country_key"] = result["country_name"].map(lambda value: normalize_country_key(value, aliases))
    result["population"] = to_nullable_integer(result["population"])
    result["area_km2"] = to_nullable_float(result["area_km2"])
    result["currencies"] = result["currencies"].map(serialize_collection)
    result["languages"] = result["languages"].map(serialize_collection)
    result["source"] = "api"
    return result.drop_duplicates(subset=["iso3"], keep="last")


def standardize_scraping(path: Path, aliases: dict[str, str]) -> pd.DataFrame:
    frame = pd.read_json(path, encoding="utf-8")
    population_column = "population_scraped" if "population_scraped" in frame.columns else "population"
    if "country_name" not in frame.columns or population_column not in frame.columns:
        raise ValueError("Source scraping: country_name ou population absent")
    result = frame[["country_name", population_column]].rename(columns={population_column: "population"}).copy()
    result["country_key"] = result["country_name"].map(lambda value: normalize_country_key(value, aliases))
    result["population"] = to_nullable_integer(result["population"])
    result["source"] = "scraping"
    return result.dropna(subset=["country_key"]).drop_duplicates(subset=["country_key"], keep="last")


def standardize_database(path: Path, aliases: dict[str, str]) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame = frame.rename(columns={"region_name": "region", "subregion_name": "subregion"})
    result = frame.reindex(columns=["iso2", "iso3", "country_name", "region", "subregion"]).copy()
    result["iso2"] = result["iso2"].map(lambda value: clean_code(value, 2))
    result["iso3"] = result["iso3"].map(lambda value: clean_code(value, 3))
    result["country_key"] = result["country_name"].map(lambda value: normalize_country_key(value, aliases))
    result["source"] = "database"
    return result.drop_duplicates(subset=["iso3"], keep="last")


def standardize_bigdata(path: Path, aliases: dict[str, str]) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "year" in frame.columns:
        frame = frame.sort_values(["iso3", "year"]).drop_duplicates("iso3", keep="last")
    result = frame.reindex(columns=["iso3", "country_name", "year", "population", "area_km2", "gdp_usd"]).copy()
    result["iso3"] = result["iso3"].map(lambda value: clean_code(value, 3))
    result["country_key"] = result["country_name"].map(lambda value: normalize_country_key(value, aliases))
    for column in ["population"]:
        result[column] = to_nullable_integer(result[column])
    for column in ["area_km2", "gdp_usd"]:
        result[column] = to_nullable_float(result[column])
    result["source"] = "bigdata"
    return result.drop_duplicates(subset=["iso3"], keep="last")


def first_non_null(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    existing = [column for column in columns if column in frame.columns]
    if not existing:
        return pd.Series(pd.NA, index=frame.index, dtype="object")
    return frame[existing].bfill(axis=1).iloc[:, 0]


def merge_sources(sources: dict[str, pd.DataFrame], config: dict[str, Any]) -> pd.DataFrame:
    if "file" not in sources:
        raise ValueError("La source fichier ISO est obligatoire comme referentiel canonique")
    canonical = sources["file"][["iso2", "iso3", "country_name", "country_key"]].copy()
    canonical = canonical.rename(columns={column: f"{column}__file" for column in canonical.columns if column != "iso3"})

    for source_name, frame in sources.items():
        if source_name == "file":
            continue
        payload = frame.copy()
        join_key = "iso3" if ("iso3" in payload.columns and payload["iso3"].notna().any()) else "country_key"
        if join_key == "iso3":
            payload = payload.drop(columns=["country_key"], errors="ignore")
        rename = {column: f"{column}__{source_name}" for column in payload.columns if column not in {join_key, "source"}}
        payload = payload.rename(columns=rename)
        canonical = canonical.merge(payload.drop(columns=["source"], errors="ignore"), how="left", on=join_key, validate="one_to_one")

    output = pd.DataFrame(index=canonical.index)
    output["iso3"] = canonical["iso3"]
    for field, priority in config["source_priority"].items():
        columns = [f"{field}__{source}" for source in priority]
        output[field] = first_non_null(canonical, columns)
    output["iso2"] = canonical.get("iso2__file")

    presence_columns = []
    source_names = []
    for source_name in sources:
        probe_options = [f"country_name__{source_name}", f"country_key__{source_name}"]
        if source_name == "file":
            probe_options = ["country_name__file"]
        probe = next((column for column in probe_options if column in canonical.columns), None)
        if probe:
            presence = canonical[probe].notna()
            presence_columns.append(presence.rename(source_name))
            source_names.append(source_name)
    presence_frame = pd.concat(presence_columns, axis=1) if presence_columns else pd.DataFrame(index=canonical.index)
    output["source_count"] = presence_frame.sum(axis=1).astype("Int64")
    output["sources"] = presence_frame.apply(lambda row: "|".join([name for name in source_names if bool(row.get(name, False))]), axis=1)

    output["population"] = to_nullable_integer(output["population"])
    output["area_km2"] = to_nullable_float(output["area_km2"])
    output["gdp_usd"] = to_nullable_float(output["gdp_usd"])
    output["density_per_km2"] = (output["population"].astype("Float64") / output["area_km2"]).round(2)
    output["gdp_per_capita_usd"] = (output["gdp_usd"] / output["population"].astype("Float64").replace(0, np.nan)).round(2)
    output["processed_at"] = datetime.now(timezone.utc).isoformat()

    columns = config["canonical_columns"]
    return output.reindex(columns=columns).sort_values("iso3").reset_index(drop=True)


def quality_report(frame: pd.DataFrame, config: dict[str, Any], sources: dict[str, pd.DataFrame]) -> dict[str, Any]:
    mandatory = config["quality"]["mandatory_columns"]
    unique = config["quality"]["unique_columns"]
    checks = {
        "mandatory_nulls": {column: int(frame[column].isna().sum()) for column in mandatory},
        "duplicates": {column: int(frame[column].duplicated().sum()) for column in unique},
        "invalid_iso2": int((frame["iso2"].astype("string").str.len() != 2).fillna(True).sum()),
        "invalid_iso3": int((frame["iso3"].astype("string").str.len() != 3).fillna(True).sum()),
        "negative_population": int((frame["population"].fillna(0) < 0).sum()),
        "non_positive_area": int((frame["area_km2"].fillna(1) <= 0).sum()),
        "rows_below_minimum_sources": int((frame["source_count"] < config["quality"]["minimum_source_count"]).sum()),
    }
    passed = (
        sum(checks["mandatory_nulls"].values()) == 0
        and sum(checks["duplicates"].values()) == 0
        and checks["invalid_iso2"] == 0
        and checks["invalid_iso3"] == 0
        and checks["negative_population"] == 0
        and checks["non_positive_area"] == 0
        and checks["rows_below_minimum_sources"] == 0
    )
    return {
        "status": "passed" if passed else "failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "final_rows": int(len(frame)),
        "source_rows": {name: int(len(source)) for name, source in sources.items()},
        "checks": checks,
    }


def discover_and_load(config: dict[str, Any], allow_missing: bool) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    aliases = {normalize_text(key): normalize_text(value) for key, value in config.get("country_aliases", {}).items()}
    specifications = {
        "file": (RAW_DIR / "file", ["countries_iso_*.csv"], standardize_file, True),
        "api": (RAW_DIR / "api", ["countries_api_*.json"], standardize_api, not allow_missing),
        "scraping": (RAW_DIR / "scraping", ["countries_scraping_*.json"], standardize_scraping, not allow_missing),
        "database": (RAW_DIR / "database", ["countries_database_*.parquet"], standardize_database, not allow_missing),
        "bigdata": (RAW_DIR / "bigdata", ["country_indicators_*.parquet"], standardize_bigdata, not allow_missing),
    }
    selected = None
    if not allow_missing:
        manifest_path = latest_file(RAW_DIR, ["manifest_*.json"])
        selected = manifest_outputs(manifest_path, set(specifications))
    sources: dict[str, pd.DataFrame] = {}
    lineage: dict[str, str] = {}
    for name, (directory, patterns, loader, required) in specifications.items():
        path = selected[name] if selected is not None else latest_file(directory, patterns, required=required)
        if path is None:
            continue
        sources[name] = loader(path, aliases)
        lineage[name] = str(path.relative_to(ROOT_DIR))
    return sources, lineage


def run(allow_missing: bool = False) -> tuple[Path, Path, Path]:
    logger = configure_logging()
    config = load_config()
    sources, lineage = discover_and_load(config, allow_missing=allow_missing)
    logger.info("C3 | sources chargees | %s", ", ".join(sources))
    final = merge_sources(sources, config)
    report = quality_report(final, config, sources)
    if report["status"] != "passed":
        raise ValueError(f"Controles qualite en echec: {report['checks']}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parquet_path = PROCESSED_DIR / f"countries_consolidated_{stamp}.parquet"
    csv_path = PROCESSED_DIR / f"countries_consolidated_{stamp}.csv"
    quality_path = QUALITY_DIR / f"c3_quality_report_{stamp}.json"
    lineage_path = QUALITY_DIR / f"c3_lineage_{stamp}.json"
    final.to_parquet(parquet_path, index=False, compression="zstd")
    final.to_csv(csv_path, index=False, encoding="utf-8")
    quality_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lineage_path.write_text(json.dumps({"generated_at": report["generated_at"], "inputs": lineage}, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("C3 | succes | lignes=%s | parquet=%s", len(final), parquet_path)
    return parquet_path, quality_path, lineage_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="C3 - harmoniser et agreger les cinq sources pays")
    parser.add_argument("--allow-missing", action="store_true", help="Autoriser les sources non encore executees pour les tests locaux")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    outputs = run(allow_missing=args.allow_missing)
    print(json.dumps({"status": "success", "outputs": [str(path) for path in outputs]}, ensure_ascii=False, indent=2))
