from __future__ import annotations

import logging

import duckdb

from src.common import ROOT_DIR, build_manifest, timestamp_slug

REQUIRED_COLUMNS = {"iso3", "country_name", "year", "population", "area_km2", "gdp_usd"}


def validate_source(connection: duckdb.DuckDBPyConnection, parquet_path: str) -> None:
    columns = {
        row[0]
        for row in connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [parquet_path]
        ).fetchall()
    }
    missing = REQUIRED_COLUMNS.difference(columns)
    if missing:
        raise ValueError(f"Colonnes Parquet obligatoires absentes: {sorted(missing)}")


def extract(settings: dict, logger: logging.Logger) -> dict:
    cfg = settings["sources"]["bigdata"]
    parquet_path = ROOT_DIR / cfg["parquet_path"]
    limit = int(cfg["limit"])
    logger.info("BIGDATA | demarrage | %s", parquet_path)
    if not parquet_path.is_file():
        raise FileNotFoundError(f"Fichier Parquet introuvable: {parquet_path}")
    if limit < 1:
        raise ValueError("La limite Big Data doit être strictement positive")

    connection = duckdb.connect(database=":memory:")
    try:
        validate_source(connection, str(parquet_path))
        frame = connection.execute(
            """
            SELECT iso3, country_name, year, population, area_km2, gdp_usd
            FROM read_parquet(?)
            WHERE iso3 IS NOT NULL AND population IS NOT NULL
            ORDER BY population DESC
            LIMIT ?
            """,
            [str(parquet_path), limit],
        ).fetch_df()
    finally:
        connection.close()

    if frame.empty:
        raise ValueError("La requête DuckDB n'a retourné aucun indicateur valide")

    output = ROOT_DIR / settings["output"]["raw_directory"] / "bigdata" / f"country_indicators_{timestamp_slug()}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False, compression="zstd")
    logger.info("BIGDATA | succes | lignes=%s | fichier=%s", len(frame), output)
    manifest = build_manifest("bigdata", output, len(frame))
    manifest["source_parquet"] = str(parquet_path.relative_to(ROOT_DIR))
    return manifest
