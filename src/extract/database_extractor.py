from __future__ import annotations

import logging
import os

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.common import ROOT_DIR, build_manifest, timestamp_slug

DEFAULT_DATABASE_URL = "postgresql+psycopg2://rncp:rncp@localhost:5432/countries"


def extract(settings: dict, logger: logging.Logger) -> dict:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    logger.info("DATABASE | demarrage | connexion PostgreSQL")
    engine = create_engine(database_url, pool_pre_ping=True)
    query = text(
        """
        SELECT iso2, iso3, country_name, region_name, subregion_name
        FROM country_reference
        WHERE active = :active
        ORDER BY iso2
        """
    )
    try:
        with engine.connect() as connection:
            frame = pd.read_sql(query, connection, params={"active": True})
    except SQLAlchemyError as exc:
        logger.exception("DATABASE | echec")
        raise RuntimeError("Echec de l'extraction PostgreSQL") from exc
    finally:
        engine.dispose()

    output = ROOT_DIR / settings["output"]["raw_directory"] / "database" / f"countries_database_{timestamp_slug()}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    logger.info("DATABASE | succes | lignes=%s | fichier=%s", len(frame), output)
    return build_manifest("database", output, len(frame))
