from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]


def load_settings(path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    config_path = ROOT_DIR / path
    with config_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def configure_logging(log_path: str | Path) -> logging.Logger:
    resolved = ROOT_DIR / log_path
    resolved.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("c1_pipeline")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
        )
        file_handler = logging.FileHandler(resolved, encoding="utf-8")
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def atomic_write_json(data: Any, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output_path.parent, delete=False, suffix=".tmp"
    ) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        temp_name = tmp.name
    os.replace(temp_name, output_path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(source: str, output_path: Path, rows: int) -> dict[str, Any]:
    return {
        "source": source,
        "output_file": str(output_path.relative_to(ROOT_DIR)),
        "rows": int(rows),
        "bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
        "extracted_at": utc_now_iso(),
        "status": "success",
    }
