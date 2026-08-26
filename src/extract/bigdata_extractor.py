from __future__ import annotations

import logging

import duckdb
import pandas as pd

from src.common import ROOT_DIR, build_manifest, timestamp_slug


def extract(settings: dict, logger: logging.Logger) -> dict:
    cfg = settings["sources"]["bigdata"]
    source_csv = ROOT_DIR / cfg["input_csv"]
    parquet_path = ROOT_DIR / cfg["parquet_path"]
    logger.info("BIGDATA | demarrage | %s", source_csv)
    if not source_csv.exists():
        raise FileNotFoundError(f"Fichier indicateurs introuvable: {source_csv}")

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(database=":memory:")
    try:
        source_sql = str(source_csv).replace("'", "''")
        parquet_sql = str(parquet_path).replace("'", "''")
        connection.execute(
            f"COPY (SELECT * FROM read_csv_auto('{source_sql}')) "
            f"TO '{parquet_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        frame = connection.execute(
            """
            SELECT iso3, country_name, year, population, area_km2, gdp_usd
            FROM read_parquet(?)
            WHERE iso3 IS NOT NULL AND population IS NOT NULL
            ORDER BY population DESC
            LIMIT ?
            """,
            [str(parquet_path), int(cfg["limit"])],
        ).fetch_df()
    finally:
        connection.close()

    output = ROOT_DIR / settings["output"]["raw_directory"] / "bigdata" / f"country_indicators_{timestamp_slug()}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False, compression="zstd")
    logger.info("BIGDATA | succes | lignes=%s | fichier=%s", len(frame), output)
    manifest = build_manifest("bigdata", output, len(frame))
    manifest["source_parquet"] = str(parquet_path.relative_to(ROOT_DIR))
    return manifest
