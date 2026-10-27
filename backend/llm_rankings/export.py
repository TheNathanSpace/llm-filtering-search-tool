"""Full local-data dump, and startup restore from another instance."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
from pydantic import BaseModel, Field

from llm_rankings.combined_models import CombinedModel
from llm_rankings.database import (
    get_all_models,
    get_all_provider_endpoints,
    replace_database,
)
from llm_rankings.provider_endpoints import ModelProviderEndpoint
from llm_rankings.refresh import (
    database_ready,
    last_refresh_at_iso,
    refresh_lock,
    set_refresh_in_progress,
    write_last_refresh_at,
)
from llm_rankings.util import get_data_dir
from llm_rankings.web_enrichment import read_lifetime_cost_usd

logger = logging.getLogger(__name__)

EXPORT_BASE_URL_ENV = "EXPORT_BASE_URL"
_USER_AGENT = "llm-filtering-search-tool/0.1"
# Connect quickly; a full cache dump can be large.
_FETCH_TIMEOUT_SECONDS = (10, 600)

# Process coordination only. A restored copy should not inherit an in-progress refresh.
_SKIP_CACHE_RELATIVE = frozenset(
    {"refresh.lock", "refresh_status.json", "enrichment.lock"}
)


class ExportedCacheFile(BaseModel):
    """One durable cache file. ``path`` is relative to ``DATA_DIR/cache``."""

    path: str
    text: str


class ExportResponse(BaseModel):
    """Snapshot of the served tables plus the caches a refresh would reuse."""

    models: list[CombinedModel]
    provider_endpoints: list[ModelProviderEndpoint]
    enrichment_cost_usd: float = Field(
        description="Lifetime USD spent on opt-in OpenRouter batch web enrichment"
    )
    last_refresh_at: str | None = Field(
        description="ISO-8601 UTC timestamp of the last successful model data refresh"
    )
    database_ready: bool = Field(
        description="True when the live model SQLite file exists"
    )
    cache_files: list[ExportedCacheFile] = Field(
        description=(
            "UTF-8 contents of DATA_DIR/cache, excluding refresh.lock, "
            "refresh_status.json, and enrichment.lock. Write each file back under DATA_DIR/cache/<path> "
            "and load models plus provider_endpoints into SQLite to reconstruct "
            "the instance without calling OpenRouter, Hugging Face, models.dev, "
            "or web enrichment."
        )
    )


def _cache_files() -> list[ExportedCacheFile]:
    cache_dir = get_data_dir() / "cache"
    if not cache_dir.is_dir():
        return []
    root = cache_dir.resolve()
    exported: list[ExportedCacheFile] = []
    for path in sorted(cache_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            continue
        relative = path.relative_to(cache_dir).as_posix()
        if relative in _SKIP_CACHE_RELATIVE:
            continue
        exported.append(ExportedCacheFile(path=relative, text=path.read_text(encoding="utf-8")))
    return exported


def build_export_response() -> ExportResponse:
    """Read the live database and durable caches. Does not call upstream APIs."""
    models = get_all_models()
    provider_endpoints = get_all_provider_endpoints()
    cache_files = _cache_files()
    logger.info(
        "Export snapshot: %d models, %d provider endpoints, %d cache files",
        len(models),
        len(provider_endpoints),
        len(cache_files),
    )
    return ExportResponse(
        models=models,
        provider_endpoints=provider_endpoints,
        enrichment_cost_usd=read_lifetime_cost_usd(),
        last_refresh_at=last_refresh_at_iso(),
        database_ready=database_ready(),
        cache_files=cache_files,
    )


def configured_export_base_url() -> str | None:
    """Public origin from ``EXPORT_BASE_URL``, without a trailing slash."""
    raw = (os.environ.get(EXPORT_BASE_URL_ENV) or "").strip()
    if not raw:
        return None
    return raw.rstrip("/")


def export_snapshot_url(base: str) -> str:
    """``{origin}/api/export`` for a scheme/host/port base URL."""
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{EXPORT_BASE_URL_ENV} must be an http(s) origin: {base}")
    if parsed.username or parsed.password:
        raise ValueError(f"{EXPORT_BASE_URL_ENV} must not include credentials: {base}")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError(f"{EXPORT_BASE_URL_ENV} must be an origin with no path: {base}")
    return f"{parsed.scheme}://{parsed.netloc}/api/export"


def _validated_cache_relative(path: str) -> str:
    if not path or path.startswith(("/", "\\")) or "\\" in path:
        raise ValueError(f"Unsafe cache path: {path}")
    parts = Path(path).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Unsafe cache path: {path}")
    return Path(*parts).as_posix()


def _cache_destination(cache_dir: Path, root: Path, relative: str) -> Path:
    destination = cache_dir
    for part in Path(relative).parts:
        destination = destination / part
        if destination.is_symlink():
            raise ValueError(f"Cache path traverses a symlink: {relative}")
    resolved = destination.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Cache path escapes DATA_DIR/cache: {relative}")
    return destination


def _restore_cache_files(files: list[ExportedCacheFile]) -> None:
    """Replace durable cache files with the snapshot. Keeps the refresh lock and status."""
    cache_dir = get_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    root = cache_dir.resolve()

    planned: list[tuple[Path, str, str]] = []
    for item in files:
        relative = _validated_cache_relative(item.path)
        if relative in _SKIP_CACHE_RELATIVE:
            logger.warning("Ignoring snapshot cache path %s", relative)
            continue
        destination = _cache_destination(cache_dir, root, relative)
        planned.append((destination, relative, item.text))

    kept = {relative for _destination, relative, _text in planned}
    for destination, _relative, text in planned:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    for path in cache_dir.rglob("*"):
        if path.is_symlink() or path.is_file():
            relative = path.relative_to(cache_dir).as_posix()
            if relative in _SKIP_CACHE_RELATIVE or relative in kept:
                continue
            path.unlink()

    directories = [path for path in cache_dir.rglob("*") if path.is_dir() and not path.is_symlink()]
    for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        if directory != cache_dir and not any(directory.iterdir()):
            directory.rmdir()


def fetch_export_snapshot(base: str) -> ExportResponse:
    """GET the source instance's public ``/api/export`` snapshot."""
    url = export_snapshot_url(base)
    logger.info("Downloading instance snapshot from %s", url)
    response = requests.get(
        url,
        timeout=_FETCH_TIMEOUT_SECONDS,
        headers={"User-Agent": _USER_AGENT},
    )
    response.raise_for_status()
    return ExportResponse.model_validate(response.json())


def apply_export_snapshot(payload: ExportResponse) -> None:
    """
    Replace the live SQLite tables and durable caches with ``payload``.

    Rows that are only in the local database are dropped. After a successful
    swap, ``last_refresh_at`` is stamped to now so startup does not immediately
    rebuild from upstream.
    """
    with refresh_lock():
        set_refresh_in_progress(in_progress=True, reason="export-import")
        try:
            _restore_cache_files(payload.cache_files)
            replace_database(payload.models, payload.provider_endpoints)
            write_last_refresh_at()
        except Exception:
            set_refresh_in_progress(in_progress=False, reason="export-import-failed")
            raise
        set_refresh_in_progress(in_progress=False, reason="export-import-done")


def import_configured_instance() -> bool:
    """
    When ``EXPORT_BASE_URL`` is set, replace local data from that instance.

    Returns False when the variable is unset. Raises when it is set and the
    download or restore fails.
    """
    base = configured_export_base_url()
    if base is None:
        return False
    payload = fetch_export_snapshot(base)
    apply_export_snapshot(payload)
    logger.info(
        "Imported instance from %s (%d models, %d provider rows, %d cache files)",
        base,
        len(payload.models),
        len(payload.provider_endpoints),
        len(payload.cache_files),
    )
    return True
