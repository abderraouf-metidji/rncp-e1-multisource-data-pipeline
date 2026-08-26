from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common import (
    ROOT_DIR,
    atomic_write_json,
    build_manifest,
    timestamp_slug,
    utc_now_iso,
)


load_dotenv(ROOT_DIR / ".env")


class ApiResponseError(RuntimeError):
    """Erreur fonctionnelle retournée par REST Countries."""


@retry(
    retry=retry_if_exception_type(
        (
            requests.Timeout,
            requests.ConnectionError,
        )
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=5,
    ),
    reraise=True,
)
def _request_json(
    url: str,
    params: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    response = requests.get(
        url=url,
        params=params,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    if "application/json" not in content_type.lower():
        raise ApiResponseError(
            "REST Countries n'a pas retourné de JSON. "
            f"Content-Type reçu : {content_type}. "
            f"URL finale : {response.url}. "
            f"Début de la réponse : {response.text[:500]}"
        )

    try:
        payload = response.json()
    except requests.JSONDecodeError as exc:
        raise ApiResponseError(
            "La réponse reçue n'est pas un JSON valide. "
            f"URL finale : {response.url}. "
            f"Début de la réponse : {response.text[:500]}"
        ) from exc

    if payload.get("success") is False:
        raise ApiResponseError(
            "REST Countries a retourné une erreur fonctionnelle. "
            f"URL finale : {response.url}. "
            f"Erreurs : {payload.get('errors')}"
        )

    return payload


def _nested_get(
    value: Any,
    *keys: str,
    default: Any = None,
) -> Any:
    current = value

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def _find_first(
    item: dict[str, Any],
    paths: list[tuple[str, ...]],
) -> Any:
    for path in paths:
        value = _nested_get(
            item,
            *path,
            default=None,
        )

        if value not in (None, "", [], {}):
            return value

    return None


def extract(
    settings: dict,
    logger: logging.Logger,
) -> dict:
    cfg = settings["sources"]["api"]

    api_key = os.getenv(
        "RESTCOUNTRIES_API_KEY",
        "rc_live_demo",
    )

    url = str(cfg["url"]).strip()
    limit = int(cfg.get("limit", 250))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": settings["project"]["user_agent"],
    }

    params = {
        "limit": limit,
    }

    logger.info(
        "API | demarrage | url=%s | limit=%s",
        url,
        limit,
    )

    payload = _request_json(
        url=url,
        params=params,
        headers=headers,
        timeout=int(
            settings["project"]["timeout_seconds"]
        ),
    )

    data = payload.get("data")

    if not isinstance(data, dict):
        raise ApiResponseError(
            "La propriété 'data' est absente "
            "ou n'est pas un objet JSON."
        )

    objects = data.get("objects")

    if not isinstance(objects, list):
        raise ApiResponseError(
            "La propriété 'data.objects' est absente "
            "ou n'est pas une liste."
        )

    normalized: list[dict[str, Any]] = []

    for item in objects:
        if not isinstance(item, dict):
            logger.warning(
                "API | élément ignoré | type=%s",
                type(item).__name__,
            )
            continue

        iso2 = _find_first(
            item,
            [
                ("codes", "alpha_2"),
                ("cca2",),
                ("alpha2Code",),
            ],
        )

        iso3 = _find_first(
            item,
            [
                ("codes", "alpha_3"),
                ("cca3",),
                ("alpha3Code",),
            ],
        )

        country_name = _find_first(
            item,
            [
                ("names", "common"),
                ("name", "common"),
                ("name",),
            ],
        )

        official_name = _find_first(
            item,
            [
                ("names", "official"),
                ("name", "official"),
            ],
        )

        capital = _find_first(
            item,
            [
                ("capital", "name"),
                ("capital",),
                ("capitals",),
            ],
        )

        if isinstance(capital, list):
            capital = capital[0] if capital else None

        region = _find_first(
            item,
            [
                ("geography", "region"),
                ("region",),
            ],
        )

        subregion = _find_first(
            item,
            [
                ("geography", "subregion"),
                ("subregion",),
            ],
        )

        population = _find_first(
            item,
            [
                ("demographics", "population"),
                ("population",),
            ],
        )

        area = _find_first(
            item,
            [
                ("geography", "area"),
                ("area",),
            ],
        )

        normalized.append(
            {
                "iso2": iso2,
                "iso3": iso3,
                "country_name": country_name,
                "official_name": official_name,
                "capital": capital,
                "region": region,
                "subregion": subregion,
                "population": population,
                "area_km2": area,
                "source_type": "api",
                "source_url": url,
                "extracted_at": utc_now_iso(),
            }
        )

    if not normalized:
        raise ApiResponseError(
            "L'API a répondu correctement, "
            "mais aucun pays n'a été extrait."
        )

    output_path = (
        ROOT_DIR
        / settings["output"]["raw_directory"]
        / "api"
        / f"countries_api_{timestamp_slug()}.json"
    )

    atomic_write_json(
        data=normalized,
        output_path=output_path,
    )

    logger.info(
        "API | succes | lignes=%s | fichier=%s",
        len(normalized),
        output_path,
    )

    return build_manifest(
        source="api",
        output_path=output_path,
        rows=len(normalized),
    )