"""Enrich models with parameter counts from the Hugging Face Hub API."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

from llm_rankings.util import get_cache_dir

logger = logging.getLogger(__name__)

HF_API_ROOT = "https://huggingface.co/api/models"
USER_AGENT = "llm-filtering-search-tool/0.1 (+https://github.com/TheNathanSpace/llm-filtering-search-tool)"
# Polite pacing for unauthenticated Hub lookups (seconds between network requests).
REQUEST_INTERVAL_SECONDS = 1.0
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 5.0


def _safe_cache_name(repo_id: str) -> str:
    return re.sub(r"[^\w.-]+", "_", repo_id) + ".json"


def _hf_cache_dir() -> Path:
    path = get_cache_dir() / "hf"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_path(repo_id: str) -> Path:
    return _hf_cache_dir() / _safe_cache_name(repo_id)


def _optional_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN")
    if token and token.strip() and not token.startswith("<"):
        return token.strip()
    return None


def _parameters_b_from_payload(payload: dict) -> float | None:
    safetensors = payload.get("safetensors")
    if not isinstance(safetensors, dict):
        return None
    total = safetensors.get("total")
    if not isinstance(total, (int, float)) or total <= 0:
        return None
    return round(float(total) / 1e9, 2)


def _load_cached(repo_id: str) -> dict | None:
    path = _cache_path(repo_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.warning("Corrupt HF cache for %s; re-fetching", repo_id)
        return None


def _write_cache(repo_id: str, payload: dict) -> None:
    _cache_path(repo_id).write_text(json.dumps(payload))


def _fetch_model_info(repo_id: str) -> dict | None:
    """
    GET Hub model info. Returns None on hard failure (404 / exhausted retries).
    Respects Retry-After on 429 and backs off exponentially.
    """
    url = f"{HF_API_ROOT}/{quote(repo_id, safe='/')}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    token = _optional_hf_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    backoff = INITIAL_BACKOFF_SECONDS
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=60)
        except requests.RequestException as exc:
            logger.warning(
                "HF request error for %s (attempt %d/%d): %s",
                repo_id,
                attempt,
                MAX_RETRIES,
                exc,
            )
            time.sleep(backoff)
            backoff *= 2
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            logger.debug("HF model not found: %s", repo_id)
            return None

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
            logger.warning(
                "HF rate-limited for %s; sleeping %.1fs (attempt %d/%d)",
                repo_id,
                wait,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(wait)
            backoff *= 2
            continue

        logger.warning(
            "HF unexpected status %s for %s: %s",
            response.status_code,
            repo_id,
            response.text[:200],
        )
        return None

    logger.warning("Giving up on HF lookup for %s after %d attempts", repo_id, MAX_RETRIES)
    return None


def parameters_b_for_repo_ids(repo_ids: set[str]) -> dict[str, float | None]:
    """
    Resolve parameter counts (billions) for Hugging Face repo ids.

    Uses on-disk cache under ``DATA_DIR/cache/hf/`` so refreshes do not re-request
    known ids. Network calls are paced and 429s are retried with backoff.
    """
    results: dict[str, float | None] = {}
    ids = sorted({rid.strip() for rid in repo_ids if rid and rid.strip()})
    if not ids:
        return results

    logger.info("Resolving HF parameter counts for %d distinct repo ids", len(ids))
    network_fetches = 0
    last_network_at = 0.0

    for repo_id in ids:
        cached = _load_cached(repo_id)
        if cached is not None:
            results[repo_id] = _parameters_b_from_payload(cached)
            continue

        # Pace only actual network requests.
        elapsed = time.time() - last_network_at
        if last_network_at and elapsed < REQUEST_INTERVAL_SECONDS:
            time.sleep(REQUEST_INTERVAL_SECONDS - elapsed)

        payload = _fetch_model_info(repo_id)
        last_network_at = time.time()
        network_fetches += 1

        if payload is None:
            # Cache a stub so we do not keep hammering missing/broken ids every refresh.
            stub = {"id": repo_id, "safetensors": None, "_cache_miss": True}
            _write_cache(repo_id, stub)
            results[repo_id] = None
            continue

        _write_cache(repo_id, payload)
        results[repo_id] = _parameters_b_from_payload(payload)

    found = sum(1 for value in results.values() if value is not None)
    logger.info(
        "HF enrichment done: %d/%d ids have parameters_b (%d network fetches)",
        found,
        len(ids),
        network_fetches,
    )
    return results
