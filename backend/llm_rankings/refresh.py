"""Model-database refresh: hard 24h auto gate plus ops-only force with selective caches."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

from llm_rankings.database import get_database_path, populate_with_models, wipe_database
from llm_rankings.util import (
    REFRESH_MAX_AGE_SECONDS,
    bootstrap_env_from_argv,
    get_cache_dir,
    is_truthy_env,
    setup_logging,
)

logger = logging.getLogger(__name__)

RefreshSource = Literal["models", "providers", "models-dev", "hf", "enrichment", "all"]

SOURCE_CHOICES: tuple[RefreshSource, ...] = (
    "models",
    "providers",
    "models-dev",
    "hf",
    "enrichment",
    "all",
)

_ATOMIC_SOURCES: frozenset[str] = frozenset(
    {"models", "providers", "models-dev", "hf", "enrichment"}
)

_WEB_ENRICHMENT_KEEP = frozenset({"cost_ledger.jsonl", "cost_summary.json"})


@dataclass(frozen=True)
class RefreshResult:
    refreshed: bool
    skipped: bool
    last_refresh_at: str | None
    detail: str


def _metadata_path() -> Path:
    return get_cache_dir() / "last_refresh.json"


def _lock_path() -> Path:
    return get_cache_dir() / "refresh.lock"


@contextmanager
def _refresh_file_lock() -> Iterator[None]:
    """Exclusive cross-process lock so API and CLI cannot wipe/rebuild concurrently."""
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


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


def normalize_force_sources(sources: frozenset[str] | None) -> frozenset[str]:
    """
    Expand CLI/API source selection to atomic cache targets.

    Empty / None / including ``all`` → every atomic source.
    Selecting ``models`` always includes ``providers`` (endpoints blob is all-or-nothing).
    """
    if not sources or "all" in sources:
        return frozenset(_ATOMIC_SOURCES)

    unknown = sources - _ATOMIC_SOURCES - {"all"}
    if unknown:
        raise ValueError(f"Unknown refresh source(s): {sorted(unknown)}")

    resolved = set(sources)
    if "models" in resolved and "providers" not in resolved:
        logger.info(
            "Also invalidating OpenRouter providers cache because models catalog was selected"
        )
        resolved.add("providers")
    return frozenset(resolved)


def _unlink_if_exists(path: Path) -> bool:
    if not path.is_file():
        return False
    path.unlink()
    logger.info("Invalidated cache file %s", path.as_posix())
    return True


def invalidate_sources(sources: frozenset[str]) -> None:
    """Delete disk caches for the given atomic sources (must already be normalized)."""
    cache = get_cache_dir()

    if "models" in sources:
        _unlink_if_exists(cache / "openrouter" / "models.json")

    if "providers" in sources:
        _unlink_if_exists(cache / "openrouter" / "endpoints.json")

    if "models-dev" in sources:
        _unlink_if_exists(cache / "models_dev" / "api.json")

    if "hf" in sources:
        hf_dir = cache / "hf"
        if hf_dir.is_dir():
            removed = 0
            for path in hf_dir.iterdir():
                if path.is_file():
                    path.unlink()
                    removed += 1
            logger.info("Invalidated %d Hugging Face cache file(s) under %s", removed, hf_dir)

    if "enrichment" in sources:
        web_dir = cache / "web_enrichment"
        if web_dir.is_dir():
            removed = 0
            for path in web_dir.iterdir():
                if path.is_file() and path.name not in _WEB_ENRICHMENT_KEEP:
                    path.unlink()
                    removed += 1
            logger.info(
                "Invalidated %d web enrichment result cache file(s) under %s "
                "(kept cost ledger/summary)",
                removed,
                web_dir,
            )
            if is_truthy_env("OR_WEB_ENRICHMENT"):
                logger.warning(
                    "OR_WEB_ENRICHMENT is enabled: forcing enrichment may re-bill OpenRouter/Exa "
                    "for models that still have gaps"
                )


def refresh_data(
    *,
    reason: str,
    force: bool = False,
    sources: frozenset[str] | None = None,
) -> RefreshResult:
    """
    Wipe and rebuild the model DB.

    When ``force`` is False (API startup/scheduler/default CLI), skip if data is fresh
    within 24h. When ``force`` is True (ops CLI), invalidate selected caches then rebuild
    regardless of the gate. Concurrent callers serialize on a cross-process file lock and
    re-check freshness after acquiring it (non-force path only).
    """
    with _refresh_file_lock():
        if not force and is_data_fresh():
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

        if force:
            targets = normalize_force_sources(sources)
            logger.info(
                "Force-refreshing model data (reason=%s, sources=%s)...",
                reason,
                ",".join(sorted(targets)),
            )
            invalidate_sources(targets)
        else:
            logger.info("Refreshing model data (reason=%s)...", reason)

        wipe_database()
        populate_with_models()
        last = write_last_refresh_at()
        detail = f"Data refreshed successfully (reason={reason}, force={force})"
        logger.info(detail)
        return RefreshResult(
            refreshed=True,
            skipped=False,
            last_refresh_at=last,
            detail=detail,
        )


def refresh_if_stale(*, reason: str) -> RefreshResult:
    """Wipe and rebuild when missing or older than 24h. No force bypass."""
    return refresh_data(reason=reason, force=False)


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m llm_rankings.refresh",
        description=(
            "Refresh the model SQLite database. Default respects the 24h freshness gate. "
            "Pass --force to wipe caches for selected sources and rebuild immediately "
            "(ops only; no public HTTP endpoint)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the 24h gate; invalidate selected caches and wipe-rebuild",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=SOURCE_CHOICES,
        dest="sources",
        metavar="SOURCE",
        help=(
            "With --force, cache to invalidate (repeatable): models, providers, models-dev, "
            "hf, enrichment, all. Default with --force is all. Selecting models also "
            "invalidates providers."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    bootstrap_env_from_argv()
    args = _parse_cli_args(argv)
    setup_logging()

    if args.sources and not args.force:
        logger.error("--source requires --force")
        return 2

    sources = frozenset(args.sources) if args.sources else None
    result = refresh_data(
        reason="cli",
        force=bool(args.force),
        sources=sources,
    )
    if result.skipped:
        logger.info(result.detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
