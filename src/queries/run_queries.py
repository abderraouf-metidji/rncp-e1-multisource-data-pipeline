from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql+psycopg2://rncp:rncp@localhost:5432/countries"
QUERY_DIR = ROOT_DIR / "database" / "queries"
RESULT_DIR = ROOT_DIR / "data" / "query_results"

QUERY_CONFIG: dict[str, dict[str, Any]] = {
    "regions": {
        "file": "01_countries_by_region.sql",
        "params": {"minimum_country_count": 1},
    },
    "indicators": {
        "file": "02_country_indicators_join.sql",
        "params": {"minimum_population": 1_000_000},
    },
    "statistics": {
        "file": "03_region_statistics.sql",
        "params": {"indicator_year": 2024, "minimum_total_population": 1_000_000},
    },
}


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("c2_queries")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        logger.addHandler(handler)
    return logger


def load_sql(filename: str) -> str:
    path = QUERY_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Requete SQL introuvable: {path}")
    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        raise ValueError(f"Requete SQL vide: {path}")
    return sql


def build_engine() -> Engine:
    return create_engine(
        os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def execute_query(engine: Engine, query_name: str, logger: logging.Logger) -> Path:
    config = QUERY_CONFIG[query_name]
    sql = load_sql(config["file"])
    logger.info("C2 | execution | requete=%s", query_name)
    with engine.connect() as connection:
        frame = pd.read_sql(text(sql), connection, params=config["params"])

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RESULT_DIR / f"{query_name}_{stamp}.csv"
    frame.to_csv(output, index=False, encoding="utf-8")
    logger.info("C2 | succes | requete=%s | lignes=%s | fichier=%s", query_name, len(frame), output)
    return output


def execute_explain(engine: Engine, logger: logging.Logger) -> Path:
    sql = load_sql("04_explain_country_indicators.sql")
    logger.info("C2 | execution | EXPLAIN ANALYZE")
    with engine.connect() as connection:
        rows = connection.execute(text(sql)).fetchall()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RESULT_DIR / f"explain_analyze_{stamp}.txt"
    output.write_text("\n".join(str(row[0]) for row in rows), encoding="utf-8")
    logger.info("C2 | succes | plan=%s", output)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executer et exporter les requetes SQL de C2")
    parser.add_argument("--query", choices=["all", *QUERY_CONFIG.keys(), "explain"], default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = configure_logging()
    engine = build_engine()
    outputs: list[str] = []
    try:
        selected = list(QUERY_CONFIG) if args.query == "all" else [args.query]
        for query_name in selected:
            if query_name == "explain":
                outputs.append(str(execute_explain(engine, logger)))
            else:
                outputs.append(str(execute_query(engine, query_name, logger)))
        if args.query == "all":
            outputs.append(str(execute_explain(engine, logger)))
    except (SQLAlchemyError, OSError, ValueError) as exc:
        logger.exception("C2 | echec | %s", exc)
        return 1
    finally:
        engine.dispose()
    print(json.dumps({"status": "success", "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
