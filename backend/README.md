# Back-end Docs

## Logging

Named loggers via `logging.getLogger(__name__)`. Call `setup_logging()` from `llm_rankings.util` once at process start (API import or a script `__main__`).

Process environment, or a `.env` file via discovery / `--env-file` / `-e` / `LLM_RANKINGS_ENV_FILE`. Values already set in the environment are kept.

| Variable | Value |
| --- | --- |
| `LOG_LEVEL` | Root logger: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `LOG_FILE_COUNT` | After the new file is created, delete oldest `DATA_DIR/logs/*.log` until at most this many remain. `latest.log` is a symlink and is not counted or deleted. |

| Output | Where |
| --- | --- |
| stdout and file | `DATA_DIR/logs/{YYYY-MM-DD}-{HHMMSS}.log` |
| Current run | `DATA_DIR/logs/latest.log` (relative symlink) |

The Next.js server appends `console.*` and request-error logs to `latest.log` (same `LOG_LEVEL`). Each line includes the logger name (module path, or `frontend` for Next.js).

## API

Vendored upstream OpenAPI: [`../api-docs/README.md`](../api-docs/README.md). Refresh with `../bin/update-external-api-docs.sh`.

| Item | Detail |
| --- | --- |
| Spec | [`../api-docs/openapi-openrouter.json`](../api-docs/openapi-openrouter.json) from https://openrouter.ai/openapi.json |
| Reference | <https://openrouter.ai/docs/api/api-reference/models/get-models> |
| Endpoints | `GET /models`, `GET /models/{author}/{slug}/endpoints` |
| Auth | `Authorization: Bearer <api-key>` |
| List shapes | `llm_rankings/or_models.py` |
| Endpoint shapes | `llm_rankings/or_endpoints.py` |
| Modalities | `input_modalities` / `output_modalities` use `InputModality` / `OutputModality` |
| Benchmarks | Embedded `benchmarks.artificial_analysis` → `benchmark_or_*` on `CombinedModel` |
| Provider rows | `model_provider_endpoints` ([SRC-10](../docs/requirements.md#src-10)) |
| This project's OpenAPI | `DATA_DIR/openapi.json` from `bin/generate-openapi-docs.sh` (default `./data/openapi.json`) |

Shapes match `api-docs/openapi-openrouter.json`.

## Pipeline

1. Load OpenRouter `GET /models` from a ≤24h cache at `DATA_DIR/cache/openrouter/models.json`, or fetch and write that cache. Always mirror `DATA_DIR/intermediate/raw/raw_or_models.json` (debug only; not a rebuild source).
2. Drop listings whose provider id starts with ``~``; whose id ends in ``:free``, ``:batch``, or ``-latest``; whose provider is ``openrouter`` (Auto, Fusion, and the other `openrouter` listings) or ``@preset``; or whose slug is ``router`` or ends with ``-router``.
3. For each remaining model, load `GET /models/{author}/{slug}/endpoints` from a ≤24h cache at `DATA_DIR/cache/openrouter/endpoints.json`, or fetch with a thread pool (default 8) and 429/5xx retries with backoff. Mirror `DATA_DIR/intermediate/raw/raw_or_endpoints.json`.
4. Fetch [models.dev](https://models.dev) `api.json`, or reuse a ≤24h cache under `DATA_DIR/cache/models_dev/`. Map that file’s `openrouter` provider `open_weights` flags by OpenRouter model id. Mirror `DATA_DIR/intermediate/raw/raw_models_dev.json`.
5. For each distinct non-empty OpenRouter `hugging_face_id`, read `safetensors.total` and store billions as `parameters_b`. Cache under `DATA_DIR/cache/hf/` (permanent per repo id; a new id fetches on miss). Use a project User-Agent, ~1s pacing, and 429 backoff. Optional `HF_TOKEN` raises Hub rate limits.
6. Map each remaining model to `CombinedModel` (`llm_rankings/combined_models.py`): identity, modalities, OpenRouter URL, embedded Artificial Analysis indices as `benchmark_or_*`, and `is_open_weights` / `parameters_b` when enrichment succeeds. Do not copy nested Design Arena rows.
7. Optional (`OR_WEB_ENRICHMENT=1`): gap-fill null `is_open_weights` and `knowledge_cutoff`, and null `parameters_b` only when the model is open weights, via OpenRouter Batch (`POST /batches`, Responses endpoint `/v1/responses`, hardcoded `openai/gpt-6-luna:batch`, OpenAI-only `web_search`). The refresh job waits until the batch completes. Never overwrite a non-null OpenRouter, models.dev, or Hugging Face value. Per-model cache (schema v2) and cost ledger/summary: `DATA_DIR/cache/web_enrichment/` (`llm_rankings/web_enrichment.py`).
8. Flatten endpoint providers into `ModelProviderEndpoint` rows (`llm_rankings/provider_endpoints.py`): $/1M input and output price, optional discount, throughput and latency percentiles for the last 30 minutes (p50, p75, p90, p99), status, uptime for the last 30 minutes, quantization, and context. Primary key ``{model_id}|{tag}``.
9. Choose one endpoint per model (`llm_rankings/provider_choice.py`): cheapest listed blend ``0.90 * input + 0.10 * output``. If the next endpoint’s latency p50 is more than 2× lower and its throughput p50 is more than 2× higher, use that endpoint. Copy its list prices, provider name, throughput p50, and latency p50 onto the model.
10. Store `models` and `model_provider_endpoints` in SQLite.

`DATA_DIR/cache/` survives `erase_data_dir()`, so a wipe does not refetch upstreams or re-bill web enrichment for known model ids.

## Refresh

Commands: [root README](../README.md#refresh-model-data). Rebuild entry points: `llm_rankings.refresh.refresh_data` (API uses `refresh_if_stale`). Requires `OR_API_KEY` in the container environment or `.env`.

| Path | Behavior |
| --- | --- |
| Automatic / default CLI | Skip when `database.db` exists and `DATA_DIR/cache/last_refresh.json` is younger than 24h. Otherwise run the pipeline (OpenRouter models, endpoints, and models.dev may come from disk cache), write a staging SQLite file, atomically replace `database.db`, then write `last_refresh_at`. The previous live DB stays readable until that swap. A skip leaves the live DB untouched and logs that data is already fresh. |
| `--force` | Bypass the 24h gate, invalidate the selected caches, then the same staging swap. |
| Export import | On API start, if `EXPORT_BASE_URL` is set. |

`--force` sources: `models`, `providers`, `models-dev`, `hf`, `enrichment`, `all` (default when `--force` has no `--source`). `models` also invalidates `providers`. API and CLI callers share `DATA_DIR/cache/refresh.lock`.

- API lifespan starts a background startup load (export import, then the gated refresh) and a refresh check about every hour. Serving is not blocked. Callers keep reading the previous snapshot while a rebuild is in flight.
- CLI: `python -m llm_rankings.refresh`, `python -m llm_rankings.database` (same CLI), or `./bin/refresh-data.sh` (via `docker exec`). No public HTTP refresh endpoint.
- `last_refresh_at` is the last successful DB rebuild, not a per-source fetch time. It resets the 24h gate.
- A successful rebuild writes `DATA_DIR/database.db.staging`, then replaces `DATA_DIR/database.db`.
- `GET /meta` and the populating empty state: [PLT-01](../docs/requirements.md#plt-01), [UI-01](../docs/requirements.md#ui-01).

`GET /export` (also `/api/export`) ([PLT-10](../docs/requirements.md#plt-10)):

- Returns metadata, every `models` row, every `model_provider_endpoints` row, and the UTF-8 text of each file under `DATA_DIR/cache` except `refresh.lock` and `refresh_status.json`
- Omits logs and `.env`

`EXPORT_BASE_URL` is an `http` or `https` origin with no path and no credentials.

- Startup downloads `{origin}/api/export` and replaces the live tables and `DATA_DIR/cache`. `refresh.lock` and `refresh_status.json` stay. Rows absent from the snapshot are dropped.
- `last_refresh_at` is stamped to now, so that start does not also rebuild from OpenRouter.
- `/meta` returns the origin as `export_base_url`. A warning at the top of the page includes that origin and stays until the variable is removed and the process restarts. The next start downloads again while the variable is set.
- A failed download is logged, and startup uses the normal refresh. The 24h refresh still runs later while the process stays up.
