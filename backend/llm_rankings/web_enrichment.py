"""Gap-fill open-weights / size via OpenRouter Batch + web search.

Opt-in with ``OR_WEB_ENRICHMENT=1``. Uses hardcoded OpenAI GPT-6 Luna batch
(``openai/gpt-6-luna:batch``) on ``POST /batches`` with the Responses wire and
provider-native ``web_search`` (Exa / OpenRouter-orchestrated search is not
available in batch). The refresh job waits for the batch; the live DB keeps
serving until staging swap. The batch id is written to ``active_batch.json``
before polling and resumed after a restart, so a new batch is not submitted
on top of a pending one. A failed batch is logged and skipped, and the
refresh continues. Never overwrites non-null OpenRouter, models.dev, or
Hugging Face values. Durable cache and cost ledger live under
``DATA_DIR/cache/web_enrichment/``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
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
# Hardcoded: OpenRouter Batch + OpenAI native web search (see product decision).
ENRICHMENT_MODEL = "openai/gpt-6-luna:batch"
BATCH_API_ENDPOINT = "/v1/responses"
BATCH_PROVIDER_ONLY = ["openai"]
CREATE_TIMEOUT_SECONDS = 300
POLL_TIMEOUT_SECONDS = 60
POLL_INITIAL_INTERVAL_SECONDS = 10.0
POLL_MAX_INTERVAL_SECONDS = 60.0
# OpenRouter may 404 briefly after a 202 while the batch becomes readable.
POLL_NOT_FOUND_GRACE_SECONDS = 120.0
# Matches OpenRouter's only supported completion_window.
POLL_MAX_WAIT_SECONDS = 24 * 60 * 60
# Bump when cache payload fields change so older entries are re-fetched when needed.
CACHE_SCHEMA_VERSION = 2
ACTIVE_BATCH_FILENAME = "active_batch.json"

TERMINAL_BATCH_STATUSES = frozenset({"completed", "failed", "expired", "cancelled"})

SYSTEM_PROMPT = (
    "Extract facts about one LLM from the web results. Definitions: "
    "is_open_weights=true only if model weights are publicly downloadable "
    "(HF, GitHub release, ModelScope, etc.), not merely an open API or "
    "open-source inference code. parameters_b = total parameter count in "
    "billions (e.g. 70 not 70000000000); for MoE prefer total over active "
    "when both appear. If unsure or sources conflict, use null — do not guess. "
    "Ignore unrelated models with similar names."
)

USER_PROMPT_TEMPLATE = (
    "OpenRouter id: {id}\n"
    "Display name: {name}\n"
    "Creator/provider: {creator}\n\n"
    "For this exact model, find: (1) whether weights are publicly downloadable, "
    "(2) total parameter count in billions. Prefer official model cards, "
    "Hugging Face, GitHub, arXiv, and vendor docs."
)

RETRY_USER_PROMPT_TEMPLATE = (
    'OpenRouter id: {id}\n'
    'Display name: {name}\n'
    'Creator/provider: {creator}\n\n'
    'Search again for "{name}" "{creator}" open weights parameter count '
    "billions model card. Prefer Hugging Face, GitHub releases, arXiv, and "
    "official vendor documentation for this exact model only."
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
            "notes": {"type": ["string", "null"]},
        },
        "required": ["is_open_weights", "parameters_b", "notes"],
    },
}


class WebEnrichmentResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_open_weights: bool | None = None
    parameters_b: float | None = None
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
        # Raw counts (e.g. 70_000_000_000) vs billions (e.g. 70, or 2400 for
        # a 2.4T MoE). Threshold must sit above plausible "already billions"
        # values — 1000 wrongly crushed trillion-scale models to ~0.
        if number >= 1_000_000:
            number = number / 1e9
        number = round(number, 2)
        return number if number > 0 else None


class _CostTracker:
    """Accumulate billed batch+web usage for one enrichment run and durable ledger."""

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
            "prompt_tokens": usage.get("prompt_tokens", usage.get("input_tokens")),
            "completion_tokens": usage.get(
                "completion_tokens", usage.get("output_tokens")
            ),
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
                "Web enrichment cost: $%.4f (%d billed items, %d cache hits; "
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


def _active_batch_path() -> Path:
    return _web_cache_dir() / ACTIVE_BATCH_FILENAME


def _read_active_batch() -> dict[str, Any] | None:
    """Return the saved batch, ``{"corrupt": True}`` when the file cannot be resumed, or None."""
    path = _active_batch_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.error(
            "Web enrichment active_batch.json is corrupt; not submitting a new batch"
        )
        return {"corrupt": True}
    if not isinstance(payload, dict):
        logger.error(
            "Web enrichment active_batch.json is unusable; not submitting a new batch"
        )
        return {"corrupt": True}
    batch_id = payload.get("batch_id")
    custom = payload.get("custom_id_to_model")
    pass_number = payload.get("pass_number")
    if not isinstance(batch_id, str) or not batch_id:
        logger.error(
            "Web enrichment active_batch.json has no batch id; not submitting a new batch"
        )
        return {"corrupt": True}
    if pass_number not in (1, 2) or not isinstance(custom, dict) or not custom:
        logger.error(
            "Web enrichment active_batch.json is unusable; not submitting a new batch"
        )
        return {"corrupt": True}
    custom_id_to_model = {
        str(key): value
        for key, value in custom.items()
        if isinstance(key, str) and isinstance(value, str)
    }
    if not custom_id_to_model:
        logger.error(
            "Web enrichment active_batch.json has no model ids; not submitting a new batch"
        )
        return {"corrupt": True}
    return {
        "batch_id": batch_id,
        "pass_number": pass_number,
        "submitted_at": payload.get("submitted_at"),
        "custom_id_to_model": custom_id_to_model,
    }


def _write_active_batch(
    *,
    batch_id: str,
    pass_number: int,
    custom_id_to_model: dict[str, str],
) -> None:
    path = _active_batch_path()
    payload = {
        "batch_id": batch_id,
        "pass_number": pass_number,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "custom_id_to_model": custom_id_to_model,
    }
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)
    logger.info(
        "Web enrichment: saved active batch %s (pass %d, %d model(s))",
        batch_id,
        pass_number,
        len(custom_id_to_model),
    )


def _clear_active_batch() -> None:
    _active_batch_path().unlink(missing_ok=True)


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
    """Return durable lifetime OpenRouter enrichment spend, or 0 if missing."""
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
        logger.warning(
            "Web enrichment [%s]: corrupt cache; re-fetching",
            model_id,
        )
        return None


def _write_cache(model_id: str, payload: dict[str, Any]) -> None:
    payload = {**payload, "schema_version": CACHE_SCHEMA_VERSION}
    _cache_path(model_id).write_text(json.dumps(payload, indent=2))


def _needs_enrichment(model: CombinedModel) -> bool:
    if model.is_open_weights is None:
        return True
    if model.is_open_weights is True and model.parameters_b is None:
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
    return False


def _merge_into_model(
    model: CombinedModel, parsed: WebEnrichmentResult
) -> tuple[bool, bool]:
    """Apply non-null fills. Returns (filled_open, filled_params)."""
    filled_open = False
    filled_params = False
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
    return filled_open, filled_params


def _parse_content(content: str | None, *, model_id: str) -> WebEnrichmentResult:
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
        logger.warning(
            "Web enrichment [%s]: failed to parse JSON content: %s",
            model_id,
            content[:200],
        )
        return WebEnrichmentResult()
    try:
        return WebEnrichmentResult.model_validate(data)
    except ValidationError as exc:
        logger.warning(
            "Web enrichment [%s]: invalid payload: %s",
            model_id,
            exc,
        )
        return WebEnrichmentResult()


def _result_from_cache(cached: dict[str, Any]) -> WebEnrichmentResult:
    try:
        return WebEnrichmentResult.model_validate(
            {
                "is_open_weights": cached.get("is_open_weights"),
                "parameters_b": cached.get("parameters_b"),
                "notes": cached.get("notes"),
            }
        )
    except ValidationError:
        return WebEnrichmentResult()


def _cache_usable_for_model(model: CombinedModel, cached: dict[str, Any]) -> bool:
    """Reject caches whose size was crushed by an old billions-vs-raw heuristic."""
    # Old heuristic treated billions > 1000 as raw counts (e.g. 2400 → 0.0).
    # Re-fetch when we still need size and a pass recorded that mangled zero.
    if model.parameters_b is None:
        cached_params = cached.get("parameters_b")
        try:
            if cached_params is not None and float(cached_params) == 0.0:
                return False
        except (TypeError, ValueError):
            return False
        for attempt in cached.get("attempts") or []:
            if not isinstance(attempt, dict):
                continue
            result = attempt.get("result")
            if not isinstance(result, dict):
                continue
            raw = result.get("parameters_b")
            try:
                if raw is not None and float(raw) == 0.0:
                    return False
            except (TypeError, ValueError):
                return False
    return True


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "HTTP-Referer": "https://github.com/TheNathanSpace/llm-filtering-search-tool",
        "X-Title": "llm-filtering-search-tool",
    }


def _responses_request_body(user_content: str) -> dict[str, Any]:
    """Per-request body for OpenRouter Batch ``/v1/responses`` + native web search."""
    return {
        "instructions": SYSTEM_PROMPT,
        "input": user_content,
        "temperature": 0,
        "tools": [{"type": "web_search"}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": RESPONSE_JSON_SCHEMA["name"],
                "strict": RESPONSE_JSON_SCHEMA["strict"],
                "schema": RESPONSE_JSON_SCHEMA["schema"],
            }
        },
    }


def _extract_response_text(payload: dict[str, Any]) -> str | None:
    """Pull assistant text from a Responses API body (``output`` / ``output_text``)."""
    output = payload.get("output")
    if not isinstance(output, list):
        # Some adapters may still return chat.completion-shaped bodies.
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        return None

    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
    if not texts:
        return None
    return "\n".join(texts)


def _normalize_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """Map Responses ``input_tokens`` / ``output_tokens`` onto chat-style keys."""
    normalized = dict(usage)
    if "prompt_tokens" not in normalized and "input_tokens" in normalized:
        normalized["prompt_tokens"] = normalized.get("input_tokens")
    if "completion_tokens" not in normalized and "output_tokens" in normalized:
        normalized["completion_tokens"] = normalized.get("output_tokens")
    if normalized.get("total_tokens") is None:
        prompt = normalized.get("prompt_tokens")
        completion = normalized.get("completion_tokens")
        if isinstance(prompt, (int, float)) or isinstance(completion, (int, float)):
            normalized["total_tokens"] = int(prompt or 0) + int(completion or 0)
    return normalized


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
        notes=second.notes or first.notes,
    )


def _submit_batch(
    *,
    api_key: str,
    requests_payload: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a batch. OpenRouter returns 202 with ``status: validating``."""
    url = form_endpoint(OR_API_ROOT, "/batches")
    # Field order: endpoint / model / provider before requests (stream-parsed body).
    body = {
        "endpoint": BATCH_API_ENDPOINT,
        "model": ENRICHMENT_MODEL,
        "provider": {
            "only": BATCH_PROVIDER_ONLY,
            "allow_fallbacks": False,
        },
        "completion_window": "24h",
        "requests": requests_payload,
    }
    try:
        response = requests.post(
            url,
            headers=_auth_headers(api_key),
            json=body,
            timeout=CREATE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Web enrichment batch submit failed: {exc}") from exc

    if response.status_code not in (200, 202):
        raise RuntimeError(
            f"Web enrichment batch submit unexpected status: "
            f"{response.status_code}: {response.text[:500]}"
        )
    payload = response.json()
    batch_id = payload.get("id")
    if not isinstance(batch_id, str) or not batch_id:
        raise RuntimeError(
            f"Web enrichment batch submit missing id: {json.dumps(payload)[:500]}"
        )
    logger.info(
        "Web enrichment: submitted batch %s (%d request(s), model=%s, endpoint=%s)",
        batch_id,
        len(requests_payload),
        ENRICHMENT_MODEL,
        BATCH_API_ENDPOINT,
    )
    return payload


def _get_batch(*, api_key: str, batch_id: str) -> tuple[int, dict[str, Any] | None, str]:
    """Return ``(status_code, json_or_none, raw_text)`` for one poll attempt."""
    url = form_endpoint(OR_API_ROOT, f"/batches/{batch_id}")
    try:
        response = requests.get(
            url,
            headers=_auth_headers(api_key),
            timeout=POLL_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Web enrichment batch poll failed ({batch_id}): {exc}"
        ) from exc

    text = response.text
    if response.status_code == 200:
        try:
            return 200, response.json(), text
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Web enrichment batch poll invalid JSON ({batch_id}): {text[:300]}"
            ) from exc
    return response.status_code, None, text


def _wait_for_batch(*, api_key: str, batch_id: str) -> dict[str, Any]:
    """Block until the batch reaches a terminal status (up to 24h)."""
    started = time.monotonic()
    interval = POLL_INITIAL_INTERVAL_SECONDS
    last_status: str | None = None

    while True:
        elapsed = time.monotonic() - started
        status_code, payload, raw_text = _get_batch(api_key=api_key, batch_id=batch_id)

        if status_code == 404:
            if elapsed < POLL_NOT_FOUND_GRACE_SECONDS:
                logger.info(
                    "Web enrichment: batch %s not readable yet (404); retrying",
                    batch_id,
                )
                time.sleep(min(interval, 5.0))
                continue
            raise RuntimeError(
                f"Web enrichment batch poll unexpected status ({batch_id}): "
                f"404: {raw_text[:500]}"
            )

        if status_code != 200 or payload is None:
            raise RuntimeError(
                f"Web enrichment batch poll unexpected status ({batch_id}): "
                f"{status_code}: {raw_text[:500]}"
            )

        status = payload.get("status")
        if not isinstance(status, str):
            raise RuntimeError(
                f"Web enrichment batch {batch_id}: missing status in "
                f"{json.dumps(payload)[:300]}"
            )

        counts = payload.get("request_counts")
        counts_note = ""
        if isinstance(counts, dict):
            counts_note = (
                f" completed={counts.get('completed')} failed={counts.get('failed')} "
                f"total={counts.get('total')}"
            )
        if status != last_status:
            logger.info(
                "Web enrichment: batch %s status=%s%s",
                batch_id,
                status,
                counts_note,
            )
            last_status = status

        if status in TERMINAL_BATCH_STATUSES:
            if status != "completed":
                error = payload.get("error")
                raise RuntimeError(
                    f"Web enrichment batch {batch_id} ended with status={status}: "
                    f"{error!r}"
                )
            return payload

        if elapsed >= POLL_MAX_WAIT_SECONDS:
            raise RuntimeError(
                f"Web enrichment batch {batch_id} still {status} after "
                f"{int(elapsed)}s (limit {POLL_MAX_WAIT_SECONDS}s)"
            )

        time.sleep(interval)
        interval = min(interval * 1.5, POLL_MAX_INTERVAL_SECONDS)


def _record_batch_costs(
    *,
    batch: dict[str, Any],
    custom_id_to_model: dict[str, str],
    costs: _CostTracker,
) -> None:
    """Prefer per-request usage costs; fall back to batch-level ``usage.cost``."""
    results = batch.get("results")
    saw_per_request_cost = False
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            custom_id = item.get("custom_id")
            model_id = (
                custom_id_to_model.get(custom_id)
                if isinstance(custom_id, str)
                else None
            )
            if model_id is None:
                continue
            response = item.get("response")
            if not isinstance(response, dict):
                continue
            body = response.get("body")
            if not isinstance(body, dict):
                continue
            raw_usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
            usage = _normalize_usage(raw_usage)
            if usage.get("cost") is None:
                continue
            saw_per_request_cost = True
            generation_id = body.get("id") if isinstance(body.get("id"), str) else None
            costs.record_usage(
                model_id=model_id,
                enrichment_model=ENRICHMENT_MODEL,
                generation_id=generation_id,
                usage=usage,
            )

    if saw_per_request_cost:
        return

    batch_usage = batch.get("usage") if isinstance(batch.get("usage"), dict) else {}
    if batch_usage.get("cost") is None:
        return
    batch_id = batch.get("id") if isinstance(batch.get("id"), str) else "unknown"
    costs.record_usage(
        model_id=f"_batch:{batch_id}",
        enrichment_model=ENRICHMENT_MODEL,
        generation_id=batch_id,
        usage=_normalize_usage(batch_usage),
    )


def _parse_batch_results(
    batch: dict[str, Any],
    *,
    custom_id_to_model: dict[str, str],
) -> dict[str, tuple[WebEnrichmentResult, dict[str, Any]]]:
    """Map custom_id → (parsed result, attempt metadata) for successful responses."""
    parsed: dict[str, tuple[WebEnrichmentResult, dict[str, Any]]] = {}
    results = batch.get("results")
    if not isinstance(results, list):
        return parsed

    for item in results:
        if not isinstance(item, dict):
            continue
        custom_id = item.get("custom_id")
        if not isinstance(custom_id, str):
            continue
        model_id = custom_id_to_model.get(custom_id)
        if model_id is None:
            continue

        error = item.get("error")
        if error is not None:
            logger.warning(
                "Web enrichment [%s]: batch item error: %s",
                model_id,
                error,
            )
            parsed[model_id] = (
                WebEnrichmentResult(),
                {"custom_id": custom_id, "error": error},
            )
            continue

        response = item.get("response")
        if not isinstance(response, dict):
            logger.warning(
                "Web enrichment [%s]: batch item missing response",
                model_id,
            )
            parsed[model_id] = (
                WebEnrichmentResult(),
                {"custom_id": custom_id, "error": "missing response"},
            )
            continue

        status_code = response.get("status_code")
        body = response.get("body")
        if status_code != 200 or not isinstance(body, dict):
            logger.warning(
                "Web enrichment [%s]: batch item status=%s body_type=%s",
                model_id,
                status_code,
                type(body).__name__,
            )
            parsed[model_id] = (
                WebEnrichmentResult(),
                {
                    "custom_id": custom_id,
                    "status_code": status_code,
                    "error": "non-200 or empty body",
                },
            )
            continue

        result = _parse_content(_extract_response_text(body), model_id=model_id)
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        meta = {
            "custom_id": custom_id,
            "generation_id": body.get("id") if isinstance(body.get("id"), str) else None,
            "cost_usd": usage.get("cost"),
            "result": result.model_dump(),
        }
        parsed[model_id] = (result, meta)

    return parsed


def _terminal_batch_failure(exc: BaseException) -> bool:
    return "ended with status=" in str(exc)


def _await_saved_batch(
    *,
    api_key: str,
    costs: _CostTracker,
    batch_id: str,
    custom_id_to_model: dict[str, str],
) -> dict[str, tuple[WebEnrichmentResult, dict[str, Any]]]:
    """Poll ``batch_id``. A terminal non-completed status clears the saved id."""
    try:
        completed = _wait_for_batch(api_key=api_key, batch_id=batch_id)
    except RuntimeError as exc:
        if _terminal_batch_failure(exc):
            logger.warning(
                "Web enrichment batch %s ended without results; clearing active batch",
                batch_id,
            )
            _clear_active_batch()
        raise
    _record_batch_costs(
        batch=completed,
        custom_id_to_model=custom_id_to_model,
        costs=costs,
    )
    return _parse_batch_results(completed, custom_id_to_model=custom_id_to_model)


def _run_enrichment_batch(
    models: list[CombinedModel],
    *,
    api_key: str,
    costs: _CostTracker,
    pass_number: int,
    prompt_template: str,
) -> dict[str, tuple[WebEnrichmentResult, dict[str, Any]]]:
    """Submit one batch for ``models``, persist its id, block until complete."""
    if not models:
        return {}

    custom_id_to_model: dict[str, str] = {}
    requests_payload: list[dict[str, Any]] = []
    for index, model in enumerate(models):
        custom_id = f"p{pass_number}-{index:04d}"
        custom_id_to_model[custom_id] = model.id
        user_content = prompt_template.format(
            id=model.id,
            name=model.name or model.id,
            creator=model.creator or "",
        )
        requests_payload.append(
            {
                "custom_id": custom_id,
                "body": _responses_request_body(user_content),
            }
        )

    logger.info(
        "Web enrichment: pass %d submitting %d model(s)",
        pass_number,
        len(models),
    )
    submitted = _submit_batch(api_key=api_key, requests_payload=requests_payload)
    batch_id = submitted["id"]
    _write_active_batch(
        batch_id=batch_id,
        pass_number=pass_number,
        custom_id_to_model=custom_id_to_model,
    )
    return _await_saved_batch(
        api_key=api_key,
        costs=costs,
        batch_id=batch_id,
        custom_id_to_model=custom_id_to_model,
    )


def enrich_combined_models(models: list[CombinedModel]) -> None:
    """
    Fill null ``is_open_weights``, and null ``parameters_b`` when the model is
    open weights, via OpenRouter Batch (GPT-6 Luna + native web search) when enabled.

    No-op unless ``OR_WEB_ENRICHMENT`` is truthy. Requires ``OR_API_KEY`` when
    enabled. Waits for batch results inside the refresh job (the live DB stays
    readable until staging swap). A failed batch, including an out-of-funds
    response, is logged and skipped. Cache hits and a successful earlier pass
    are kept. Mutates ``models`` in place; never overwrites non-null upstream
    values.
    """
    if not web_enrichment_enabled():
        logger.info("Web enrichment skipped (OR_WEB_ENRICHMENT not enabled)")
        return
    try:
        _apply_web_enrichment(models)
    except Exception:
        logger.exception(
            "Web enrichment failed; continuing refresh without enrichment"
        )


def _remember_pass(
    parsed: dict[str, tuple[WebEnrichmentResult, dict[str, Any]]],
    *,
    model_ids: list[str],
    pass_number: int,
    results_by_id: dict[str, WebEnrichmentResult],
    attempts_by_id: dict[str, list[dict[str, Any]]],
    merge: bool,
) -> None:
    for model_id in model_ids:
        result, meta = parsed.get(
            model_id, (WebEnrichmentResult(), {"error": "missing from batch"})
        )
        if merge and model_id in results_by_id:
            results_by_id[model_id] = _merge_parsed_passes(
                results_by_id[model_id], result
            )
            attempts_by_id.setdefault(model_id, []).append(
                {"pass": pass_number, **meta}
            )
        else:
            results_by_id[model_id] = result
            attempts_by_id[model_id] = [{"pass": pass_number, **meta}]


def _write_result_caches(
    model_ids: list[str],
    *,
    results_by_id: dict[str, WebEnrichmentResult],
    attempts_by_id: dict[str, list[dict[str, Any]]],
) -> None:
    for model_id in model_ids:
        parsed = results_by_id.get(model_id, WebEnrichmentResult())
        _write_cache(
            model_id,
            {
                "model_id": model_id,
                "is_open_weights": parsed.is_open_weights,
                "parameters_b": parsed.parameters_b,
                "notes": parsed.notes,
                "enrichment_model": ENRICHMENT_MODEL,
                "attempts": attempts_by_id.get(model_id, []),
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "_cache_miss": (
                    parsed.is_open_weights is None and parsed.parameters_b is None
                ),
            },
        )


def _maybe_pass_two(
    retry_models: list[CombinedModel],
    *,
    api_key: str,
    costs: _CostTracker,
    results_by_id: dict[str, WebEnrichmentResult],
    attempts_by_id: dict[str, list[dict[str, Any]]],
) -> None:
    if not retry_models:
        _clear_active_batch()
        return
    logger.info(
        "Web enrichment: %d model(s) still have gaps; submitting retry batch",
        len(retry_models),
    )
    try:
        second_pass = _run_enrichment_batch(
            retry_models,
            api_key=api_key,
            costs=costs,
            pass_number=2,
            prompt_template=RETRY_USER_PROMPT_TEMPLATE,
        )
    except Exception:
        logger.exception("Web enrichment pass 2 failed; keeping pass 1 results")
        return
    retry_ids = [model.id for model in retry_models]
    _remember_pass(
        second_pass,
        model_ids=retry_ids,
        pass_number=2,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
        merge=True,
    )
    _write_result_caches(
        retry_ids,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
    )
    _clear_active_batch()


def _submit_passes(
    to_fetch: list[CombinedModel],
    *,
    api_key: str,
    costs: _CostTracker,
    results_by_id: dict[str, WebEnrichmentResult],
    attempts_by_id: dict[str, list[dict[str, Any]]],
) -> None:
    try:
        first_pass = _run_enrichment_batch(
            to_fetch,
            api_key=api_key,
            costs=costs,
            pass_number=1,
            prompt_template=USER_PROMPT_TEMPLATE,
        )
    except Exception:
        logger.exception(
            "Web enrichment pass 1 failed; continuing without new enrichment results"
        )
        return
    fetch_ids = [model.id for model in to_fetch]
    _remember_pass(
        first_pass,
        model_ids=fetch_ids,
        pass_number=1,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
        merge=False,
    )
    _write_result_caches(
        fetch_ids,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
    )
    retry_models = [
        model
        for model in to_fetch
        if _gaps_remain(model, results_by_id[model.id])
    ]
    _maybe_pass_two(
        retry_models,
        api_key=api_key,
        costs=costs,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
    )


def _resume_or_block_submit(
    active: dict[str, Any],
    *,
    models: list[CombinedModel],
    api_key: str,
    costs: _CostTracker,
    results_by_id: dict[str, WebEnrichmentResult],
    attempts_by_id: dict[str, list[dict[str, Any]]],
) -> None:
    """Poll the saved batch. Do not submit a different batch in this run."""
    if active.get("corrupt"):
        logger.error(
            "Web enrichment active batch file is unusable; not submitting a new batch"
        )
        return
    batch_id = active["batch_id"]
    pass_number = active["pass_number"]
    custom_id_to_model: dict[str, str] = active["custom_id_to_model"]
    logger.info(
        "Web enrichment: resuming batch %s (pass %s); not submitting a new batch",
        batch_id,
        pass_number,
    )
    try:
        resumed = _await_saved_batch(
            api_key=api_key,
            costs=costs,
            batch_id=batch_id,
            custom_id_to_model=custom_id_to_model,
        )
    except Exception:
        logger.exception(
            "Web enrichment resume of batch %s failed; not submitting a new batch",
            batch_id,
        )
        return
    batch_ids = list(dict.fromkeys(custom_id_to_model.values()))
    _remember_pass(
        resumed,
        model_ids=batch_ids,
        pass_number=pass_number,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
        merge=pass_number == 2,
    )
    _write_result_caches(
        batch_ids,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
    )
    if pass_number == 2:
        _clear_active_batch()
        return
    by_model = {model.id: model for model in models}
    retry_models = [
        by_model[model_id]
        for model_id in batch_ids
        if model_id in by_model
        and _gaps_remain(by_model[model_id], results_by_id[model_id])
    ]
    _maybe_pass_two(
        retry_models,
        api_key=api_key,
        costs=costs,
        results_by_id=results_by_id,
        attempts_by_id=attempts_by_id,
    )


def _apply_web_enrichment(models: list[CombinedModel]) -> None:
    api_key = get_env_var("OR_API_KEY")

    candidates = [m for m in models if _needs_enrichment(m)]
    active = _read_active_batch()
    if not candidates and active is None:
        logger.info("Web enrichment: no models with open-weights or size gaps")
        return

    logger.info(
        "Web enrichment: %d candidate model(s) (batch_model=%s, endpoint=%s, "
        "provider=%s)",
        len(candidates),
        ENRICHMENT_MODEL,
        BATCH_API_ENDPOINT,
        ",".join(BATCH_PROVIDER_ONLY),
    )
    costs = _CostTracker()
    filled_open = 0
    filled_params = 0

    results_by_id: dict[str, WebEnrichmentResult] = {}
    attempts_by_id: dict[str, list[dict[str, Any]]] = {}
    to_fetch: list[CombinedModel] = []

    for model in candidates:
        cached = _load_cached(model.id)
        if cached is not None and _cache_usable_for_model(model, cached):
            costs.record_cache_hit()
            results_by_id[model.id] = _result_from_cache(cached)
            continue
        if cached is not None:
            logger.info(
                "Web enrichment [%s]: cache stale (schema); re-fetching",
                model.id,
            )
        to_fetch.append(model)

    if active is not None:
        _resume_or_block_submit(
            active,
            models=models,
            api_key=api_key,
            costs=costs,
            results_by_id=results_by_id,
            attempts_by_id=attempts_by_id,
        )
    elif to_fetch:
        _submit_passes(
            to_fetch,
            api_key=api_key,
            costs=costs,
            results_by_id=results_by_id,
            attempts_by_id=attempts_by_id,
        )

    for model in candidates:
        parsed = results_by_id.get(model.id, WebEnrichmentResult())
        open_filled, params_filled = _merge_into_model(model, parsed)
        if open_filled:
            filled_open += 1
        if params_filled:
            filled_params += 1

    costs.finalize()
    logger.info(
        "Web enrichment done: filled is_open_weights=%d, parameters_b=%d",
        filled_open,
        filled_params,
    )
