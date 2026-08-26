from __future__ import annotations

import argparse
import sys

from src.common import ROOT_DIR, atomic_write_json, configure_logging, load_settings, timestamp_slug
from src.extract import api_extractor, bigdata_extractor, database_extractor, file_extractor, scraping_extractor

EXTRACTORS = {
    "api": api_extractor.extract,
    "scraping": scraping_extractor.extract,
    "file": file_extractor.extract,
    "database": database_extractor.extract,
    "bigdata": bigdata_extractor.extract,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline RNCP C1 - extraction multi-sources des pays")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["all", *EXTRACTORS.keys()],
        default=["all"],
        help="Sources a extraire",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Poursuivre les autres extractions lorsqu'une source echoue",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings()
    logger = configure_logging(settings["output"]["log_file"])
    selected = list(EXTRACTORS) if "all" in args.sources else args.sources
    run_manifest = {"run_id": timestamp_slug(), "results": [], "errors": []}

    for source in selected:
        try:
            run_manifest["results"].append(EXTRACTORS[source](settings, logger))
        except Exception as exc:
            logger.exception("PIPELINE | source=%s | echec", source)
            run_manifest["errors"].append({"source": source, "error": str(exc)})
            if not args.continue_on_error:
                break

    manifest_path = ROOT_DIR / "data" / "raw" / f"manifest_{run_manifest['run_id']}.json"
    atomic_write_json(run_manifest, manifest_path)
    logger.info(
        "PIPELINE | termine | succes=%s | erreurs=%s | manifest=%s",
        len(run_manifest["results"]),
        len(run_manifest["errors"]),
        manifest_path,
    )
    return 1 if run_manifest["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
