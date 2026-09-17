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

RESPONSE_FIELDS = ",".join(
    (
        "codes.alpha_2", "codes.alpha_3", "names.common", "names.official",
        "capitals", "region", "subregion", "population", "area",
        "currencies", "languages",
    )
)


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

    if not isinstance(payload, dict):
        raise ApiResponseError("La réponse JSON doit être un objet")

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


def _collection_values(value: Any, field: str) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value)
    if not isinstance(value, list):
        return []
    values = []
    for entry in value:
        label = entry.get(field) if isinstance(entry, dict) else entry
        if isinstance(label, str) and label.strip():
            values.append(label.strip())
    return sorted(set(values))


def extract(
    settings: dict,
    logger: logging.Logger,
) -> dict:
    cfg = settings["sources"]["api"]

    api_key = os.getenv("RESTCOUNTRIES_API_KEY", "").strip()
    if not api_key or api_key in {"rc_live_demo", "replace_with_your_api_key"}:
        raise ValueError(
            "RESTCOUNTRIES_API_KEY doit contenir une vraie cle API : "
            "la cle de demonstration ne retourne qu'un exemple."
        )

    url = str(cfg["url"]).strip()
    page_size = int(cfg.get("page_size", 100))
    if not 1 <= page_size <= 100:
        raise ValueError("page_size doit etre compris entre 1 et 100")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": settings["project"]["user_agent"],
    }

    logger.info(
        "API | demarrage | url=%s | page_size=%s",
        url,
        page_size,
    )

    objects: list[Any] = []
    offset = 0
    while True:
        payload = _request_json(
            url=url,
            params={"limit": page_size, "offset": offset, "response_fields": RESPONSE_FIELDS},
            headers=headers,
            timeout=int(settings["project"]["timeout_seconds"]),
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiResponseError("La propriété 'data' est absente ou invalide")
        page_objects = data.get("objects")
        meta = data.get("meta")
        if not isinstance(page_objects, list) or not isinstance(meta, dict):
            raise ApiResponseError("La réponse doit contenir data.objects et data.meta")
        if not isinstance(meta.get("more"), bool):
            raise ApiResponseError("La réponse doit contenir data.meta.more")
        if meta.get("more") and not page_objects:
            raise ApiResponseError("Pagination incohérente : page vide avec meta.more=true")
        objects.extend(page_objects)
        if not meta.get("more"):
            break
        offset += len(page_objects)

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
        if isinstance(capital, dict):
            capital = capital.get("name")

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
        if isinstance(area, dict):
            area = area.get("kilometers")

        currencies = _collection_values(item.get("currencies"), "code")
        languages = _collection_values(item.get("languages"), "name")

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
                "currencies": currencies,
                "languages": languages,
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
