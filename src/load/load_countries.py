from __future__ import annotations

import argparse
import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
SCHEMA_PATH = ROOT_DIR / "database" / "c4_schema.sql"
DEFAULT_DATABASE_URL = "postgresql+psycopg2://rncp:rncp@localhost:5432/countries"

MANDATORY_COLUMNS = {"iso2", "iso3", "country_name", "source_count", "sources", "processed_at"}


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("c4_load")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        logger.addHandler(handler)
    return logger


def latest_consolidated_file() -> Path:
    candidates = list(PROCESSED_DIR.glob("countries_consolidated_*.parquet"))
    if not candidates:
        raise FileNotFoundError("Aucun fichier countries_consolidated_*.parquet dans data/processed")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_frame(frame: pd.DataFrame) -> None:
    missing = MANDATORY_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Colonnes obligatoires absentes: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Le fichier consolidé est vide")
    if frame[list(MANDATORY_COLUMNS)].isna().any().any():
        raise ValueError("Des valeurs obligatoires sont manquantes")
    if frame["iso2"].astype(str).str.fullmatch(r"[A-Z]{2}").eq(False).any():
        raise ValueError("Au moins un code ISO2 est invalide")
    if frame["iso3"].astype(str).str.fullmatch(r"[A-Z]{3}").eq(False).any():
        raise ValueError("Au moins un code ISO3 est invalide")
    if frame["iso2"].duplicated().any() or frame["iso3"].duplicated().any():
        raise ValueError("Des codes ISO sont dupliqués")


def execute_schema(engine: Engine) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        cursor.execute(sql)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def clean_optional(value: Any) -> Any:
    return None if pd.isna(value) else value


def upsert_region(connection: Connection, region_name: str | None) -> int | None:
    if not region_name:
        return None
    return connection.execute(
        text("""
            INSERT INTO region (region_name)
            VALUES (:region_name)
            ON CONFLICT (region_name)
            DO UPDATE SET region_name = EXCLUDED.region_name
            RETURNING region_id
        """),
        {"region_name": region_name},
    ).scalar_one()


def upsert_subregion(connection: Connection, region_id: int | None, subregion_name: str | None) -> int | None:
    if region_id is None or not subregion_name:
        return None
    return connection.execute(
        text("""
            INSERT INTO subregion (region_id, subregion_name)
            VALUES (:region_id, :subregion_name)
            ON CONFLICT (region_id, subregion_name)
            DO UPDATE SET subregion_name = EXCLUDED.subregion_name
            RETURNING subregion_id
        """),
        {"region_id": region_id, "subregion_name": subregion_name},
    ).scalar_one()


def upsert_country(connection: Connection, row: pd.Series, region_id: int | None, subregion_id: int | None) -> tuple[int, bool]:
    existed = connection.execute(
        text("SELECT country_id FROM country WHERE iso3 = :iso3"),
        {"iso3": row["iso3"]},
    ).scalar_one_or_none()
    country_id = connection.execute(
        text("""
            INSERT INTO country (
                region_id, subregion_id, iso2, iso3, country_name, official_name,
                capital, currencies, languages, source_count, sources, processed_at
            ) VALUES (
                :region_id, :subregion_id, :iso2, :iso3, :country_name, :official_name,
                :capital, :currencies, :languages, :source_count, :sources, :processed_at
            )
            ON CONFLICT (iso3) DO UPDATE SET
                region_id = EXCLUDED.region_id,
                subregion_id = EXCLUDED.subregion_id,
                iso2 = EXCLUDED.iso2,
                country_name = EXCLUDED.country_name,
                official_name = EXCLUDED.official_name,
                capital = EXCLUDED.capital,
                currencies = EXCLUDED.currencies,
                languages = EXCLUDED.languages,
                source_count = EXCLUDED.source_count,
                sources = EXCLUDED.sources,
                processed_at = EXCLUDED.processed_at,
                loaded_at = CURRENT_TIMESTAMP
            RETURNING country_id
        """),
        {
            "region_id": region_id,
            "subregion_id": subregion_id,
            "iso2": row["iso2"],
            "iso3": row["iso3"],
            "country_name": row["country_name"],
            "official_name": clean_optional(row.get("official_name")),
            "capital": clean_optional(row.get("capital")),
            "currencies": clean_optional(row.get("currencies")),
            "languages": clean_optional(row.get("languages")),
            "source_count": int(row["source_count"]),
            "sources": row["sources"],
            "processed_at": pd.Timestamp(row["processed_at"]).to_pydatetime(),
        },
    ).scalar_one()
    return country_id, existed is not None


def upsert_indicator(connection: Connection, country_id: int, row: pd.Series, indicator_year: int) -> bool:
    values = [row.get("population"), row.get("area_km2"), row.get("gdp_usd")]
    if all(pd.isna(value) for value in values):
        return False
    connection.execute(
        text("""
            INSERT INTO country_indicator (
                country_id, indicator_year, population, area_km2, gdp_usd,
                density_per_km2, gdp_per_capita_usd
            ) VALUES (
                :country_id, :indicator_year, :population, :area_km2, :gdp_usd,
                :density_per_km2, :gdp_per_capita_usd
            )
            ON CONFLICT (country_id, indicator_year) DO UPDATE SET
                population = EXCLUDED.population,
                area_km2 = EXCLUDED.area_km2,
                gdp_usd = EXCLUDED.gdp_usd,
                density_per_km2 = EXCLUDED.density_per_km2,
                gdp_per_capita_usd = EXCLUDED.gdp_per_capita_usd,
                loaded_at = CURRENT_TIMESTAMP
        """),
        {
            "country_id": country_id,
            "indicator_year": indicator_year,
            "population": clean_optional(row.get("population")),
            "area_km2": clean_optional(row.get("area_km2")),
            "gdp_usd": clean_optional(row.get("gdp_usd")),
            "density_per_km2": clean_optional(row.get("density_per_km2")),
            "gdp_per_capita_usd": clean_optional(row.get("gdp_per_capita_usd")),
        },
    )
    return True


def load_file(engine: Engine, source_file: Path, indicator_year: int, logger: logging.Logger) -> dict[str, Any]:
    frame = pd.read_parquet(source_file)
    validate_frame(frame)
    load_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)
    source_hash = sha256_file(source_file)
    counters = {"rows_read": len(frame), "countries_inserted": 0, "countries_updated": 0, "indicators_upserted": 0}

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO data_load_audit (
                    load_id, source_file, source_sha256, started_at, status, rows_read
                ) VALUES (
                    :load_id, :source_file, :source_sha256, :started_at, 'started', :rows_read
                )
            """),
            {"load_id": load_id, "source_file": str(source_file), "source_sha256": source_hash, "started_at": started_at, "rows_read": len(frame)},
        )

    try:
        with engine.begin() as connection:
            for _, row in frame.iterrows():
                region_id = upsert_region(connection, clean_optional(row.get("region")))
                subregion_id = upsert_subregion(connection, region_id, clean_optional(row.get("subregion")))
                country_id, existed = upsert_country(connection, row, region_id, subregion_id)
                counters["countries_updated" if existed else "countries_inserted"] += 1
                if upsert_indicator(connection, country_id, row, indicator_year):
                    counters["indicators_upserted"] += 1
            connection.execute(
                text("""
                    UPDATE data_load_audit
                    SET completed_at = :completed_at,
                        status = 'success',
                        countries_inserted = :countries_inserted,
                        countries_updated = :countries_updated,
                        indicators_upserted = :indicators_upserted
                    WHERE load_id = :load_id
                """),
                {"completed_at": datetime.now(timezone.utc), "load_id": load_id, **{k: v for k, v in counters.items() if k != "rows_read"}},
            )
    except Exception as exc:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE data_load_audit
                    SET completed_at = :completed_at, status = 'failed', error_message = :error_message
                    WHERE load_id = :load_id
                """),
                {"completed_at": datetime.now(timezone.utc), "error_message": str(exc)[:4000], "load_id": load_id},
            )
        raise

    logger.info("C4 | chargement réussi | %s", counters)
    return {"load_id": str(load_id), "source_sha256": source_hash, **counters}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="C4 - charger le jeu consolidé dans PostgreSQL")
    parser.add_argument("--input", type=Path, default=None, help="Fichier Parquet C3 ; le plus récent par défaut")
    parser.add_argument("--indicator-year", type=int, default=2024)
    parser.add_argument("--skip-schema", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = configure_logging()
    source_file = args.input or latest_consolidated_file()
    if not source_file.is_absolute():
        source_file = ROOT_DIR / source_file
    engine = create_engine(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL), pool_pre_ping=True)
    try:
        if not args.skip_schema:
            execute_schema(engine)
        result = load_file(engine, source_file, args.indicator_year, logger)
        print(result)
        return 0
    except (OSError, ValueError, SQLAlchemyError) as exc:
        logger.exception("C4 | échec | %s", exc)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
