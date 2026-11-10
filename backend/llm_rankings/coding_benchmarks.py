"""Coding score: 60% FrontierCode 2.0 and 40% Terminal-Bench 4.0.

Both upstream scores are fractions. The stored blend is that mix in percent,
rounded to one decimal, for the effort whose intelligence index matches the
catalog value at one decimal. Those same rounded inputs are stored as
``benchmark_coding_frontier`` and ``benchmark_coding_terminal``. A tie keeps
the higher intelligence, then the higher Terminal-Bench score. The score is
set only when both inputs exist.

Fetches run when the live snapshot has no ``benchmark_coding`` column, the
database is empty, a kept model id is new, a live intelligence value is null
and the incoming row has one, a stored coding score is missing either input,
or a previous fetch failed and every stored coding score is null. An
intelligence change on an existing value does not fetch. A skipped run copies
stored scores and leaves the error file alone. A failed fetch keeps stored
scores and records a short error. A successful fetch replaces every score,
including null where a model does not match, and clears the error.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from llm_rankings.combined_models import CombinedModel
from llm_rankings.or_models import OpenRouterModel
from llm_rankings.util import get_cache_dir

logger = logging.getLogger(__name__)

TERMINAL_BENCH_URL = "https://openrouter.ai/api/frontend/v1/private/artificial-analysis-benchmarks/all"
FRONTIER_CODE_PAGE = "https://artificialanalysis.ai/evaluations/frontiercode-2-0"
_FETCH_TIMEOUT_SECONDS = 30
_ERROR_MESSAGE = "Coding benchmark fetch failed."
_TENTH = Decimal("0.1")
_MANIFEST = re.compile(
    r'manifest\\?":\s*\{\\?"path\\?":\s*\\?"([^"\\]+)\\?"\s*,\s*\\?"key\\?":\s*\\?"([0-9a-fA-F]+)\\?"'
)


@dataclass(frozen=True)
class LiveCodingRow:
    id: str
    intelligence: float | None
    coding: float | None
    frontier: float | None = None
    terminal: float | None = None


@dataclass(frozen=True)
class CodingScore:
    frontier: float
    terminal: float
    blended: float


@dataclass(frozen=True)
class EffortScore:
    aa_id: str
    intelligence: float | None
    terminal: float | None


def round_tenth(value: float) -> Decimal:
    return Decimal(str(value)).quantize(_TENTH, rounding=ROUND_HALF_UP)


def coding_score(frontier_fraction: float, terminal_fraction: float) -> CodingScore:
    """Round both fraction scores to one-decimal percents and blend them."""
    frontier = round_tenth(frontier_fraction * 100)
    terminal = round_tenth(terminal_fraction * 100)
    blended = (Decimal("0.6") * frontier + Decimal("0.4") * terminal).quantize(_TENTH, rounding=ROUND_HALF_UP)
    return CodingScore(float(frontier), float(terminal), float(blended))


def coding_percent(frontier_fraction: float, terminal_fraction: float) -> float:
    """Blend the two fraction scores into a one-decimal percentage."""
    return coding_score(frontier_fraction, terminal_fraction).blended


def matching_effort(rows: list[EffortScore], intelligence: float | None) -> EffortScore | None:
    """Effort whose intelligence rounds to the catalog value.

    Several matches keep the higher raw intelligence, then the higher
    Terminal-Bench fraction.
    """
    if intelligence is None:
        return None
    target = round_tenth(intelligence)
    matches = [row for row in rows if row.intelligence is not None and round_tenth(row.intelligence) == target]
    if not matches:
        return None

    def sort_key(row: EffortScore) -> tuple[float, float]:
        terminal = row.terminal if row.terminal is not None else float("-inf")
        return (row.intelligence if row.intelligence is not None else float("-inf"), terminal)

    matches.sort(key=sort_key, reverse=True)
    return matches[0]


def coding_for_slug(
    slug: str | None,
    intelligence: float | None,
    efforts_by_slug: dict[str, list[EffortScore]],
    frontier_by_id: dict[str, float],
) -> CodingScore | None:
    if not slug:
        return None
    chosen = matching_effort(efforts_by_slug.get(slug, []), intelligence)
    if chosen is None or chosen.terminal is None:
        return None
    frontier = frontier_by_id.get(chosen.aa_id)
    if frontier is None:
        return None
    return coding_score(frontier, chosen.terminal)


def fetch_needed(
    live: list[LiveCodingRow],
    incoming: list[CombinedModel],
    *,
    coding_column_present: bool,
    retry_empty_failure: bool,
    components_incomplete: bool = False,
) -> bool:
    if not coding_column_present or not live or retry_empty_failure or components_incomplete:
        return True
    by_id = {row.id: row for row in live}
    for model in incoming:
        previous = by_id.get(model.id)
        if previous is None:
            return True
        if previous.intelligence is None and model.benchmark_or_intelligence_index is not None:
            return True
    return False


def copy_stored_coding(models: list[CombinedModel], live: list[LiveCodingRow]) -> None:
    by_id = {row.id: row for row in live}
    for model in models:
        stored = by_id.get(model.id)
        model.benchmark_coding = None if stored is None else stored.coding
        model.benchmark_coding_frontier = None if stored is None else stored.frontier
        model.benchmark_coding_terminal = None if stored is None else stored.terminal


def terminal_rows(payload: dict) -> dict[str, list[EffortScore]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Terminal-Bench payload has no data list")
    grouped: dict[str, list[EffortScore]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        slug = row.get("permaslug")
        aa_id = row.get("aa_id")
        if not isinstance(slug, str) or not isinstance(aa_id, str):
            continue
        benchmark_data = row.get("benchmark_data")
        evaluations = benchmark_data.get("evaluations") if isinstance(benchmark_data, dict) else None
        if not isinstance(evaluations, dict):
            evaluations = {}
        grouped.setdefault(slug, []).append(
            EffortScore(
                aa_id=aa_id,
                intelligence=_number(evaluations.get("artificial_analysis_intelligence_index")),
                terminal=_number(evaluations.get("terminalbench_v4_0")),
            )
        )
    return grouped


def frontier_scores(payload: dict, aa_ids: set[str]) -> dict[str, float]:
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("FrontierCode payload has no models list")
    scores: dict[str, float] = {}
    for model in models:
        if not isinstance(model, dict):
            continue
        model_id = model.get("id")
        if not isinstance(model_id, str) or model_id not in aa_ids:
            continue
        score = _number(model.get("frontierCode20"))
        if score is not None:
            scores[model_id] = score
    return scores


def parse_frontier_manifest(html: str) -> tuple[str, str]:
    match = _MANIFEST.search(html)
    if match is None:
        raise ValueError("FrontierCode page has no data manifest")
    path, key = match.group(1), match.group(2)
    if path.startswith(("http://", "https://")):
        return path, key
    return "https://artificialanalysis.ai" + (path if path.startswith("/") else f"/{path}"), key


def decrypt_frontier_blob(blob: bytes, key_hex: str) -> dict:
    key = bytes.fromhex(key_hex)
    iv = hashlib.sha256(key).digest()[:12]
    plain = gzip.decompress(AESGCM(key).decrypt(iv, blob, None))
    payload = json.loads(plain)
    if not isinstance(payload, dict):
        raise ValueError("FrontierCode payload is not an object")
    return payload


def read_coding_benchmark_error() -> str | None:
    path = _error_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Ignoring unreadable coding benchmark error file %s", path.as_posix())
        return None
    if not isinstance(payload, dict):
        return None
    message = payload.get("error")
    if not isinstance(message, str) or not message.strip():
        return None
    return message


def write_coding_benchmark_error(message: str | None) -> None:
    path = _error_path()
    if message is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"error": message}) + "\n", encoding="utf-8")


def apply_coding_benchmarks(models: list[CombinedModel], or_models: list[OpenRouterModel]) -> None:
    """Fill ``benchmark_coding`` before the live database is replaced."""
    slug_by_id = {model.id: model.canonical_slug for model in or_models}
    column_present, live = _read_live_coding_rows()
    retry_empty_failure = bool(read_coding_benchmark_error()) and all(row.coding is None for row in live)
    incomplete = any(row.coding is not None and (row.frontier is None or row.terminal is None) for row in live)
    if not fetch_needed(
        live,
        models,
        coding_column_present=column_present,
        retry_empty_failure=retry_empty_failure,
        components_incomplete=incomplete,
    ):
        copy_stored_coding(models, live)
        logger.info("Coding benchmark fetch skipped; kept %d stored score(s)", len(live))
        return
    try:
        efforts = terminal_rows(_get_json(TERMINAL_BENCH_URL))
        aa_ids = {row.aa_id for rows in efforts.values() for row in rows}
        page = _get_text(FRONTIER_CODE_PAGE)
        data_url, key = parse_frontier_manifest(page)
        frontier = frontier_scores(decrypt_frontier_blob(_get_bytes(data_url), key), aa_ids)
        scored = 0
        for model in models:
            score = coding_for_slug(
                slug_by_id.get(model.id),
                model.benchmark_or_intelligence_index,
                efforts,
                frontier,
            )
            model.benchmark_coding = None if score is None else score.blended
            model.benchmark_coding_frontier = None if score is None else score.frontier
            model.benchmark_coding_terminal = None if score is None else score.terminal
            if score is not None:
                scored += 1
        write_coding_benchmark_error(None)
        logger.info("Coding benchmarks updated (%d scored, %d models)", scored, len(models))
    except Exception:
        logger.exception("Coding benchmark fetch failed")
        copy_stored_coding(models, live)
        write_coding_benchmark_error(_ERROR_MESSAGE)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _error_path() -> Path:
    return get_cache_dir() / "openrouter" / "coding_benchmark_error.json"


def _read_live_coding_rows() -> tuple[bool, list[LiveCodingRow]]:
    from llm_rankings.database import get_database_path

    path = get_database_path()
    if not path.is_file():
        return False, []
    connection = sqlite3.connect(path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "models" not in tables:
            return False, []
        columns = {row[1] for row in connection.execute("PRAGMA table_info(models)").fetchall()}
        present = "benchmark_coding" in columns
        coding_sql = "benchmark_coding" if present else "NULL"
        frontier_sql = "benchmark_coding_frontier" if "benchmark_coding_frontier" in columns else "NULL"
        terminal_sql = "benchmark_coding_terminal" if "benchmark_coding_terminal" in columns else "NULL"
        query = f"SELECT id, benchmark_or_intelligence_index, {coding_sql}, {frontier_sql}, {terminal_sql} FROM models"
        rows = [
            LiveCodingRow(row_id, intelligence, coding, frontier, terminal)
            for row_id, intelligence, coding, frontier, terminal in connection.execute(query)
            if isinstance(row_id, str)
        ]
        return present, rows
    finally:
        connection.close()


def _get_json(url: str) -> dict:
    payload = _get(url).json()
    if not isinstance(payload, dict):
        raise ValueError(f"Coding benchmark response from {url} is not an object")
    return payload


def _get_text(url: str) -> str:
    return _get(url).text


def _get_bytes(url: str) -> bytes:
    return _get(url).content


def _get(url: str) -> requests.Response:
    response = requests.get(url, timeout=_FETCH_TIMEOUT_SECONDS, headers={"User-Agent": "llm-rankings"})
    if response.status_code != 200:
        raise ValueError(f"Coding benchmark request failed ({response.status_code}) for {url}")
    return response
