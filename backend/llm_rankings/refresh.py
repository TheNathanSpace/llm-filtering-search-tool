"""Hard 24h refresh gate for wipe-and-rebuild of the model database."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from llm_rankings.database import get_database_path, populate_with_models, wipe_database
from llm_rankings.util import REFRESH_MAX_AGE_SECONDS, get_cache_dir

logger = logging.getLogger(__name__)

_REFRESH_LOCK = threading.Lock()


@dataclass(frozen=True)
class RefreshResult:
    refreshed: bool
    skipped: bool
    last_refresh_at: str | None
    detail: str


def _metadata_path() -> Path:
    return get_cache_dir() / "last_refresh.json"


def read_last_refresh_at() -> datetime | None:
    path = _metadata_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.warning("Corrupt refresh metadata at %s; treating as missing", path.as_posix())
        return None
    raw = payload.get("last_refresh_at")
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        logger.warning("Invalid last_refresh_at in %s: %s", path.as_posix(), raw)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def write_last_refresh_at(when: datetime | None = None) -> str:
    stamp = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
    iso = stamp.isoformat()
    path = _metadata_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_refresh_at": iso}, indent=2) + "\n")
    return iso


def last_refresh_at_iso() -> str | None:
    stamp = read_last_refresh_at()
    return stamp.isoformat() if stamp is not None else None


def is_data_fresh() -> bool:
    """True when SQLite exists and the last successful refresh was within 24h."""
    if not get_database_path().exists():
        return False
    stamp = read_last_refresh_at()
    if stamp is None:
        return False
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    return age < REFRESH_MAX_AGE_SECONDS


def refresh_if_stale(*, reason: str) -> RefreshResult:
    """
    Wipe and rebuild the model DB when missing or older than 24h.

    Hard cap: no force bypass. Concurrent callers serialize on a process lock and
    re-check freshness after acquiring it.
    """
    with _REFRESH_LOCK:
        if is_data_fresh():
            last = last_refresh_at_iso()
            detail = (
                f"Data already refreshed within the last {REFRESH_MAX_AGE_SECONDS // 3600} hours "
                f"(reason={reason})"
            )
            logger.info(detail)
            return RefreshResult(
                refreshed=False,
                skipped=True,
                last_refresh_at=last,
                detail=detail,
            )

        logger.info("Refreshing model data (reason=%s)...", reason)
        wipe_database()
        populate_with_models()
        last = write_last_refresh_at()
        detail = f"Data refreshed successfully (reason={reason})"
        logger.info(detail)
        return RefreshResult(
            refreshed=True,
            skipped=False,
            last_refresh_at=last,
            detail=detail,
        )
