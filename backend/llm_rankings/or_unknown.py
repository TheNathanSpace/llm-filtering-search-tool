"""Unrecognized attributes from a live OpenRouter fetch.

Cache hits do not rewrite this file. Ignored keys are dropped by ``model_dump()``,
so a cache read would otherwise clear a warning for attributes the last upstream
payload still contained.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from llm_rankings.util import get_cache_dir

logger = logging.getLogger(__name__)

_SOURCES = ("models", "endpoints")


def _path() -> Path:
    return get_cache_dir() / "openrouter" / "unknown_attributes.json"


def _empty() -> dict[str, list[str]]:
    return {source: [] for source in _SOURCES}


def _read() -> dict[str, list[str]]:
    path = _path()
    if not path.is_file():
        return _empty()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Ignoring unreadable OpenRouter unknown-attribute file %s", path.as_posix())
        return _empty()
    if not isinstance(payload, dict):
        return _empty()
    parsed = _empty()
    for source in _SOURCES:
        raw = payload.get(source) or []
        if not isinstance(raw, list):
            continue
        parsed[source] = [item for item in raw if isinstance(item, str)]
    return parsed


def record_openrouter_unknown(source: str, attributes: list[str]) -> None:
    """Replace the saved names for ``models`` or ``endpoints``."""
    if source not in _SOURCES:
        raise ValueError(f"Unknown OpenRouter source: {source}")
    current = _read()
    names = sorted(set(attributes))
    current[source] = names
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    if names:
        logger.warning(
            "OpenRouter %s response included unrecognized attributes: %s",
            source,
            ", ".join(names),
        )


def read_openrouter_unknown_attributes() -> list[str]:
    """Names from the last live models fetch, then the last live endpoints fetch."""
    current = _read()
    seen: list[str] = []
    for source in _SOURCES:
        for name in current[source]:
            if name not in seen:
                seen.append(name)
    return seen
