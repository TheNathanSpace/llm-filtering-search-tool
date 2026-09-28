"""Fetch and parse models.dev open-weights flags for OpenRouter model ids."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import requests
from pydantic import BaseModel, ConfigDict

from llm_rankings.util import get_cache_dir, get_raw_data_dir

logger = logging.getLogger(__name__)

MODELS_DEV_API_URL = "https://models.dev/api.json"
USER_AGENT = "llm-filtering-search-tool/0.1 (+https://github.com/TheNathanSpace/llm-filtering-search-tool)"
# Reuse the full catalog across refreshes so we do not re-hit models.dev every wipe.
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60


class ModelsDevModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    open_weights: bool


def _cache_path() -> Path:
    return get_cache_dir() / "models_dev" / "api.json"


def _cache_is_fresh(path: Path) -> bool:
    if not path.is_file():
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_MAX_AGE_SECONDS


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _fetch_api_json() -> dict:
    logger.info("Fetching models.dev catalog from %s", MODELS_DEV_API_URL)
    response = requests.get(
        MODELS_DEV_API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=120,
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to retrieve models.dev catalog: {response.status_code} - {response.text[:500]}")
    return response.json()


def get_models_dev_payload(*, force_refresh: bool = False) -> dict:
    """
    Return the models.dev ``api.json`` payload.

    Uses a 24h on-disk cache under ``DATA_DIR/cache/models_dev/`` so repeated refresh
    cycles do not re-download the multi-megabyte catalog. Always mirrors a copy under
    ``DATA_DIR/intermediate/raw/`` for debugging the current run.
    """
    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if force_refresh or not _cache_is_fresh(cache_path):
        payload = _fetch_api_json()
        cache_path.write_text(json.dumps(payload))
        logger.debug("Wrote models.dev cache to %s", cache_path.as_posix())
    else:
        logger.info("Using cached models.dev catalog (%s)", cache_path.as_posix())
        payload = _load_json(cache_path)

    raw_path = get_raw_data_dir() / "raw_models_dev.json"
    raw_path.write_text(json.dumps(payload, indent=4))
    logger.debug("Wrote models.dev raw dump to %s", raw_path.as_posix())
    return payload


def open_weights_by_openrouter_id(payload: dict | None = None) -> dict[str, bool]:
    """
    Map OpenRouter model id → ``open_weights`` from the models.dev ``openrouter`` provider.

    Unknown / unmatched ids are simply absent from the returned dict.
    """
    if payload is None:
        payload = get_models_dev_payload()

    openrouter = payload.get("openrouter")
    if not isinstance(openrouter, dict):
        logger.warning("models.dev payload missing 'openrouter' provider")
        return {}

    models = openrouter.get("models")
    if not isinstance(models, dict):
        logger.warning("models.dev openrouter entry missing 'models'")
        return {}

    result: dict[str, bool] = {}
    for model_id, raw in models.items():
        try:
            model = ModelsDevModel.model_validate(raw)
        except Exception:
            logger.debug("Skipping unparseable models.dev entry: %s", model_id)
            continue
        result[model.id] = model.open_weights

    logger.info("Parsed open_weights for %d models.dev OpenRouter entries", len(result))
    return result
