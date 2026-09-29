"""Gap-fill open-weights / size / knowledge cutoff via OpenRouter chat + Exa.

Opt-in with ``OR_WEB_ENRICHMENT=1`` and ``OR_ENRICHMENT_MODEL``. Never overwrites
non-null OpenRouter, models.dev, or Hugging Face values. Durable cache and cost
ledger live under ``DATA_DIR/cache/web_enrichment/``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from llm_rankings.combined_models import CombinedModel
from llm_rankings.retrieve_data import OR_API_ROOT, form_endpoint
from llm_rankings.util import get_cache_dir, get_env_var

logger = logging.getLogger(__name__)

USER_AGENT = "llm-filtering-search-tool/0.1 (+https://github.com/TheNathanSpace/llm-filtering-search-tool)"
MAX_WORKERS = 2
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 120
EXA_MAX_RESULTS = 10
# Bump when cache payload fields change so older entries are re-fetched when needed.
CACHE_SCHEMA_VERSION = 2

SYSTEM_PROMPT = (
    "Extract facts about one LLM from the web results. Definitions: "
    "is_open_weights=true only if model weights are publicly downloadable "
    "(HF, GitHub release, ModelScope, etc.), not merely an open API or "
    "open-source inference code. parameters_b = total parameter count in "
    "billions (e.g. 70 not 70000000000); for MoE prefer total over active "
    "when both appear. knowledge_cutoff = the model's training-data knowledge "
    "cutoff as YYYY-MM-DD (not the release/announce date). If unsure or "
    "sources conflict, use null — do not guess. Ignore unrelated models with "
    "similar names."
)

USER_PROMPT_TEMPLATE = (
    "OpenRouter id: {id}\n"
    "Display name: {name}\n"
    "Creator/provider: {creator}\n\n"
    "For this exact model, find: (1) whether weights are publicly downloadable, "
    "(2) total parameter count in billions, (3) knowledge cutoff date "
    "(YYYY-MM-DD). Prefer official model cards, Hugging Face, GitHub, arXiv, "
    "and vendor docs."
)

RETRY_USER_PROMPT_TEMPLATE = (
    'OpenRouter id: {id}\n'
    'Display name: {name}\n'
    'Creator/provider: {creator}\n\n'
    'Search again for "{name}" "{creator}" open weights parameter count '
    "billions knowledge cutoff YYYY-MM-DD model card. Prefer Hugging Face, "
    "GitHub releases, arXiv, and official vendor documentation for this exact "
    "model only."
)

RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "name": "model_web_enrichment",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_open_weights": {"type": ["boolean", "null"]},
            "parameters_b": {"type": ["number", "null"]},
            "knowledge_cutoff": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
        },
        "required": ["is_open_weights", "parameters_b", "knowledge_cutoff", "notes"],
    },
}


def _parse_cutoff_to_ms(value: object) -> float | None:
    """Parse a knowledge-cutoff date into epoch milliseconds (UTC midnight)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Already ms (or seconds): treat large values as ms, small as seconds.
        number = float(value)
        if number <= 0:
            return None
        if number < 1e12:
            number *= 1000.0
        return number
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return parsed.timestamp() * 1000.0
        except ValueError:
            continue
    return None


class WebEnrichmentResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_open_weights: bool | None = None
    parameters_b: float | None = None
    # Epoch milliseconds (same as CombinedModel.knowledge_cutoff).
    knowledge_cutoff: float | None = None
    notes: str | None = None

    @field_validator("parameters_b", mode="before")
    @classmethod
    def _normalize_parameters_b(cls, value: object) -> float | None:
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number <= 0:
            return None
        # Heuristic: raw parameter counts instead of billions.
        if number > 1000:
            number = number / 1e9
        return round(number, 2)

    @field_validator("knowledge_cutoff", mode="before")
    @classmethod
    def _normalize_knowledge_cutoff(cls, value: object) -> float | None:
        return _parse_cutoff_to_ms(value)


class _CostTracker:
    """Accumulate billed chat+web usage for one enrichment run and durable ledger."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.run_usd = 0.0
        self.run_inference_usd = 0.0
        self.run_tool_usd = 0.0
        self.network_calls = 0
        self.cache_hits = 0

    def record_cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1

    def record_usage(
        self,
        *,
        model_id: str,
        enrichment_model: str,
        generation_id: str | None,
        usage: dict[str, Any],
    ) -> dict[str, Any]:
        cost = usage.get("cost")
        try:
            cost_f = float(cost) if cost is not None else 0.0
        except (TypeError, ValueError):
            cost_f = 0.0

        details = usage.get("cost_details") if isinstance(usage.get("cost_details"), dict) else {}
        inference = 0.0
        if details.get("upstream_inference_cost") is not None:
            try:
                inference = float(details["upstream_inference_cost"])
            except (TypeError, ValueError):
                inference = 0.0
        else:
            for key in (
                "upstream_inference_prompt_cost",
                "upstream_inference_completions_cost",
            ):
                raw = details.get(key)
                try:
                    if raw is not None:
                        inference += float(raw)
                except (TypeError, ValueError):
                    pass

        tool_raw = details.get("server_tool_cost")
        try:
            tool_f = float(tool_raw) if tool_raw is not None else 0.0
        except (TypeError, ValueError):
            tool_f = 0.0

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "model_id": model_id,
            "enrichment_model": enrichment_model,
            "generation_id": generation_id,
            "cost_usd": cost_f,
            "cost_details": details,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

        with self._lock:
            self.network_calls += 1
            self.run_usd += cost_f
            self.run_inference_usd += inference
            self.run_tool_usd += tool_f
            _append_cost_ledger(entry)
        return entry

    def finalize(self) -> None:
        with self._lock:
            _update_cost_summary(
                last_run_usd=self.run_usd,
                last_run_calls=self.network_calls,
                add_lifetime_usd=self.run_usd,
                add_lifetime_calls=self.network_calls,
            )
            logger.info(
                "web enrichment cost: $%.4f (%d network calls, %d cache hits; "
                "inference=$%.4f search/tools=$%.4f)",
                self.run_usd,
                self.network_calls,
                self.cache_hits,
                self.run_inference_usd,
                self.run_tool_usd,
            )


def _truthy_env(name: str) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def web_enrichment_enabled() -> bool:
    return _truthy_env("OR_WEB_ENRICHMENT")


def _safe_cache_name(model_id: str) -> str:
    return re.sub(r"[^\w.-]+", "_", model_id) + ".json"


def _web_cache_dir() -> Path:
    path = get_cache_dir() / "web_enrichment"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_path(model_id: str) -> Path:
    return _web_cache_dir() / _safe_cache_name(model_id)


def _ledger_path() -> Path:
    return _web_cache_dir() / "cost_ledger.jsonl"


def _summary_path() -> Path:
    return _web_cache_dir() / "cost_summary.json"


_ledger_lock = threading.Lock()


def _append_cost_ledger(entry: dict[str, Any]) -> None:
    with _ledger_lock:
        with _ledger_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")


def _update_cost_summary(
    *,
    last_run_usd: float,
    last_run_calls: int,
    add_lifetime_usd: float,
    add_lifetime_calls: int,
) -> None:
    path = _summary_path()
    with _ledger_lock:
        existing: dict[str, Any] = {}
        if path.is_file():
            try:
                existing = json.loads(path.read_text())
            except json.JSONDecodeError:
                logger.warning("Corrupt web enrichment cost_summary.json; resetting rollup")
        lifetime_usd = float(existing.get("lifetime_usd") or 0.0) + add_lifetime_usd
        lifetime_calls = int(existing.get("lifetime_calls") or 0) + add_lifetime_calls
        payload = {
            "lifetime_usd": round(lifetime_usd, 6),
            "lifetime_calls": lifetime_calls,
            "last_run_usd": round(last_run_usd, 6),
            "last_run_calls": last_run_calls,
            "last_run_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(payload, indent=2))


def read_lifetime_cost_usd() -> float:
    """Return durable lifetime Exa/OpenRouter enrichment spend, or 0 if missing."""
    path = _summary_path()
    if not path.is_file():
        return 0.0
    with _ledger_lock:
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupt web enrichment cost_summary.json; reporting $0")
            return 0.0
    try:
        return float(payload.get("lifetime_usd") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _load_cached(model_id: str) -> dict[str, Any] | None:
    path = _cache_path(model_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.warning("Corrupt web enrichment cache for %s; re-fetching", model_id)
        return None


def _write_cache(model_id: str, payload: dict[str, Any]) -> None:
    payload = {**payload, "schema_version": CACHE_SCHEMA_VERSION}
    _cache_path(model_id).write_text(json.dumps(payload, indent=2))


def _needs_enrichment(model: CombinedModel) -> bool:
    if model.is_open_weights is None:
        return True
    if model.is_open_weights is True and model.parameters_b is None:
        return True
    if model.knowledge_cutoff is None:
        return True
    return False


def _gaps_remain(model: CombinedModel, parsed: WebEnrichmentResult) -> bool:
    """True if merging ``parsed`` into ``model`` would still leave an eligible gap."""
    open_flag = (
        model.is_open_weights if model.is_open_weights is not None else parsed.is_open_weights
    )
    if open_flag is None:
        return True
    params = model.parameters_b
    if params is None and open_flag is True:
        params = parsed.parameters_b
    if open_flag is True and params is None:
        return True
    cutoff = (
        model.knowledge_cutoff
        if model.knowledge_cutoff is not None
        else parsed.knowledge_cutoff
    )
    if cutoff is None:
        return True
    return False


def _merge_into_model(
    model: CombinedModel, parsed: WebEnrichmentResult
) -> tuple[bool, bool, bool]:
    """Apply non-null fills. Returns (filled_open, filled_params, filled_cutoff)."""
    filled_open = False
    filled_params = False
    filled_cutoff = False
    if model.is_open_weights is None and parsed.is_open_weights is not None:
        model.is_open_weights = parsed.is_open_weights
        filled_open = True
    effective_open = model.is_open_weights
    if (
        effective_open is True
        and model.parameters_b is None
        and parsed.parameters_b is not None
    ):
        model.parameters_b = parsed.parameters_b
        filled_params = True
    if model.knowledge_cutoff is None and parsed.knowledge_cutoff is not None:
        model.knowledge_cutoff = parsed.knowledge_cutoff
        filled_cutoff = True
    return filled_open, filled_params, filled_cutoff


def _parse_content(content: str | None) -> WebEnrichmentResult:
    if not content or not content.strip():
        return WebEnrichmentResult()
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse web enrichment JSON content: %s", content[:200])
        return WebEnrichmentResult()
    try:
        return WebEnrichmentResult.model_validate(data)
    except ValidationError as exc:
        logger.warning("Invalid web enrichment payload: %s", exc)
        return WebEnrichmentResult()


def _result_from_cache(cached: dict[str, Any]) -> WebEnrichmentResult:
    try:
        return WebEnrichmentResult.model_validate(
            {
                "is_open_weights": cached.get("is_open_weights"),
                "parameters_b": cached.get("parameters_b"),
                "knowledge_cutoff": cached.get("knowledge_cutoff"),
                "notes": cached.get("notes"),
            }
        )
    except ValidationError:
        return WebEnrichmentResult()


def _cache_usable_for_model(model: CombinedModel, cached: dict[str, Any]) -> bool:
    """Reject stale caches that predate fields we still need (e.g. knowledge_cutoff)."""
    version = int(cached.get("schema_version") or 1)
    if model.knowledge_cutoff is None and (
        version < 2 or "knowledge_cutoff" not in cached
    ):
        return False
    return True


def _chat_completion(
    *,
    api_key: str,
    enrichment_model: str,
    user_content: str,
) -> dict[str, Any]:
    url = form_endpoint(OR_API_ROOT, "/chat/completions")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "HTTP-Referer": "https://github.com/TheNathanSpace/llm-filtering-search-tool",
        "X-Title": "llm-filtering-search-tool",
    }
    body = {
        "model": enrichment_model,
        "temperature": 0,
        "plugins": [
            {
                "id": "web",
                "engine": "exa",
                "max_results": EXA_MAX_RESULTS,
                "exclude_domains": ["reddit.com"],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": RESPONSE_JSON_SCHEMA,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }

    backoff = INITIAL_BACKOFF_SECONDS
    last_error: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                url, headers=headers, json=body, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.RequestException as exc:
            last_error = str(exc)
            logger.warning(
                "Web enrichment request error (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            time.sleep(backoff)
            backoff *= 2
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
            logger.warning(
                "Web enrichment rate-limited; sleeping %.1fs (attempt %d/%d)",
                wait,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(wait)
            backoff *= 2
            continue

        if response.status_code in (500, 502, 503, 504):
            last_error = f"{response.status_code}: {response.text[:200]}"
            logger.warning(
                "Web enrichment server error %s (attempt %d/%d)",
                response.status_code,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(backoff)
            backoff *= 2
            continue

        last_error = f"{response.status_code}: {response.text[:300]}"
        logger.warning("Web enrichment unexpected status: %s", last_error)
        break

    raise RuntimeError(f"Web enrichment chat failed after retries: {last_error}")


def _extract_message_content(payload: dict[str, Any]) -> str | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    return None


def _merge_parsed_passes(
    first: WebEnrichmentResult, second: WebEnrichmentResult
) -> WebEnrichmentResult:
    return WebEnrichmentResult(
        is_open_weights=(
            first.is_open_weights
            if first.is_open_weights is not None
            else second.is_open_weights
        ),
        parameters_b=(
            first.parameters_b if first.parameters_b is not None else second.parameters_b
        ),
        knowledge_cutoff=(
            first.knowledge_cutoff
            if first.knowledge_cutoff is not None
            else second.knowledge_cutoff
        ),
        notes=second.notes or first.notes,
    )


def _fetch_for_model(
    model: CombinedModel,
    *,
    api_key: str,
    enrichment_model: str,
    costs: _CostTracker,
) -> WebEnrichmentResult:
    user_content = USER_PROMPT_TEMPLATE.format(
        id=model.id,
        name=model.name or model.id,
        creator=model.creator or "",
    )
    payload = _chat_completion(
        api_key=api_key,
        enrichment_model=enrichment_model,
        user_content=user_content,
    )
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    cost_entry = costs.record_usage(
        model_id=model.id,
        enrichment_model=enrichment_model,
        generation_id=payload.get("id") if isinstance(payload.get("id"), str) else None,
        usage=usage,
    )
    parsed = _parse_content(_extract_message_content(payload))
    attempts = [
        {
            "pass": 1,
            "generation_id": cost_entry.get("generation_id"),
            "cost_usd": cost_entry.get("cost_usd"),
            "result": parsed.model_dump(),
        }
    ]

    if _gaps_remain(model, parsed):
        retry_content = RETRY_USER_PROMPT_TEMPLATE.format(
            id=model.id,
            name=model.name or model.id,
            creator=model.creator or "",
        )
        logger.info("Web enrichment retry for %s (gaps remain after first pass)", model.id)
        try:
            retry_payload = _chat_completion(
                api_key=api_key,
                enrichment_model=enrichment_model,
                user_content=retry_content,
            )
        except RuntimeError as exc:
            logger.warning("Web enrichment retry failed for %s: %s", model.id, exc)
            retry_payload = None

        if retry_payload is not None:
            retry_usage = (
                retry_payload.get("usage")
                if isinstance(retry_payload.get("usage"), dict)
                else {}
            )
            retry_cost = costs.record_usage(
                model_id=model.id,
                enrichment_model=enrichment_model,
                generation_id=(
                    retry_payload.get("id")
                    if isinstance(retry_payload.get("id"), str)
                    else None
                ),
                usage=retry_usage,
            )
            retry_parsed = _parse_content(_extract_message_content(retry_payload))
            attempts.append(
                {
                    "pass": 2,
                    "generation_id": retry_cost.get("generation_id"),
                    "cost_usd": retry_cost.get("cost_usd"),
                    "result": retry_parsed.model_dump(),
                }
            )
            parsed = _merge_parsed_passes(parsed, retry_parsed)

    cache_payload = {
        "model_id": model.id,
        "is_open_weights": parsed.is_open_weights,
        "parameters_b": parsed.parameters_b,
        "knowledge_cutoff": parsed.knowledge_cutoff,
        "notes": parsed.notes,
        "enrichment_model": enrichment_model,
        "attempts": attempts,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "_cache_miss": (
            parsed.is_open_weights is None
            and parsed.parameters_b is None
            and parsed.knowledge_cutoff is None
        ),
    }
    _write_cache(model.id, cache_payload)
    return parsed


def enrich_combined_models(models: list[CombinedModel]) -> None:
    """
    Fill null ``is_open_weights`` / ``parameters_b`` / ``knowledge_cutoff`` via
    OpenRouter + Exa when enabled.

    No-op unless ``OR_WEB_ENRICHMENT`` is truthy. Requires ``OR_ENRICHMENT_MODEL``
    and ``OR_API_KEY`` when enabled. Mutates ``models`` in place; never overwrites
    non-null upstream values.
    """
    if not web_enrichment_enabled():
        logger.info("Web enrichment skipped (OR_WEB_ENRICHMENT not enabled)")
        return

    enrichment_model = get_env_var("OR_ENRICHMENT_MODEL").strip()
    if not enrichment_model or enrichment_model.startswith("<"):
        raise ValueError(
            "OR_ENRICHMENT_MODEL must be set to an OpenRouter model id when "
            "OR_WEB_ENRICHMENT is enabled"
        )
    api_key = get_env_var("OR_API_KEY")

    candidates = [m for m in models if _needs_enrichment(m)]
    if not candidates:
        logger.info("Web enrichment: no models with open-weights/size/cutoff gaps")
        return

    logger.info(
        "Web enrichment: %d candidate model(s) (model=%s, exa max_results=%d)",
        len(candidates),
        enrichment_model,
        EXA_MAX_RESULTS,
    )
    costs = _CostTracker()
    filled_open = 0
    filled_params = 0
    filled_cutoff = 0

    def _process(model: CombinedModel) -> tuple[str, WebEnrichmentResult, bool]:
        cached = _load_cached(model.id)
        if cached is not None and _cache_usable_for_model(model, cached):
            costs.record_cache_hit()
            return model.id, _result_from_cache(cached), True
        if cached is not None:
            logger.info(
                "Web enrichment cache stale for %s (schema); re-fetching", model.id
            )
        try:
            result = _fetch_for_model(
                model,
                api_key=api_key,
                enrichment_model=enrichment_model,
                costs=costs,
            )
        except RuntimeError as exc:
            logger.warning("Web enrichment failed for %s: %s", model.id, exc)
            stub = {
                "model_id": model.id,
                "is_open_weights": None,
                "parameters_b": None,
                "knowledge_cutoff": None,
                "notes": f"error: {exc}",
                "enrichment_model": enrichment_model,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "_cache_miss": True,
            }
            _write_cache(model.id, stub)
            return model.id, WebEnrichmentResult(), False
        return model.id, result, False

    by_id = {m.id: m for m in candidates}
    total = len(candidates)
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_process, m) for m in candidates]
        for future in as_completed(futures):
            model_id, parsed, from_cache = future.result()
            done += 1
            cache_note = " [cached]" if from_cache else ""
            logger.info(
                "Web enrichment for %s (%d/%d)%s",
                model_id,
                done,
                total,
                cache_note,
            )
            model = by_id[model_id]
            open_filled, params_filled, cutoff_filled = _merge_into_model(model, parsed)
            if open_filled:
                filled_open += 1
            if params_filled:
                filled_params += 1
            if cutoff_filled:
                filled_cutoff += 1

    costs.finalize()
    logger.info(
        "Web enrichment done: filled is_open_weights=%d, parameters_b=%d, "
        "knowledge_cutoff=%d",
        filled_open,
        filled_params,
        filled_cutoff,
    )
