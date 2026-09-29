# Back-end Docs

## Logging

Back-end modules use named loggers via `logging.getLogger(__name__)`. Call `setup_logging()` from
`llm_rankings.util` once at process start (API import or a script `__main__`).

Configuration (from `.env`, or an explicit path via `--env-file` / `-e` or
`LLM_RANKINGS_ENV_FILE`):

- `LOG_LEVEL` — root logger level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`)
- `LOG_FILE_COUNT` — after creating the new file, delete oldest `DATA_DIR/logs/*.log` files until
  at most this many remain (`latest.log` is a symlink and is not counted/deleted)

Output goes to both stdout and `DATA_DIR/logs/{YYYY-MM-DD}-{HHMMSS}.log`. `DATA_DIR/logs/latest.log`
is a relative symlink to the current run's file. The Next.js server also appends its `console.*` /
request-error logs to `latest.log` (same `LOG_LEVEL` filter). Log lines include the logger name
(module path, or `frontend` for Next.js).

## API Details

Vendored upstream OpenAPI (refresh with `../bin/update-external-api-docs.sh`; see
[`../api-docs/README.md`](../api-docs/README.md)):

- OpenRouter: [`../api-docs/openapi-openrouter.json`](../api-docs/openapi-openrouter.json)
  (from https://openrouter.ai/openapi.json)

- OpenRouter:
  - API reference: <https://openrouter.ai/docs/api/api-reference/models/get-models>
  - Key endpoints: `GET /models`, `GET /models/{author}/{slug}/endpoints`
  - Authentication: `Authorization: Bearer <api-key>` header
  - Response shapes: `llm_rankings/or_models.py` (Models list) and
    `llm_rankings/or_endpoints.py` (per-provider endpoints), aligned with
    `api-docs/openapi-openrouter.json`. Architecture `input_modalities` /
    `output_modalities` use the `InputModality` / `OutputModality` enums.
    Embedded `benchmarks.artificial_analysis` indices become `benchmark_or_*` on
    `CombinedModel`. Per-provider pricing and throughput/latency go to
    `model_provider_endpoints` ([SRC-10](../docs/requirements.md#src-10)).
  - This project's FastAPI OpenAPI export (for the front-end client) is written to
    `DATA_DIR/openapi.json` by `bin/generate-openapi-docs.sh` (default `./data/openapi.json`).

## Building the model table (OpenRouter + enrichment)

1. Load OpenRouter `GET /models` from a ≤24h cache under `DATA_DIR/cache/openrouter/models.json`,
   or fetch and write that cache; always mirror under `DATA_DIR/intermediate/raw/raw_or_models.json`
   (debug only; not a rebuild source).
2. Drop OpenRouter models whose provider id starts with ``~`` (router/variant listings) or whose id
   ends with ``:free`` (free-tier variants).
3. For each remaining model, load `GET /models/{author}/{slug}/endpoints` from a ≤24h cache under
   `DATA_DIR/cache/openrouter/endpoints.json`, or fetch with a bounded thread pool (default 8
   workers) and 429/5xx retries with backoff. Mirror raw payloads to
   `DATA_DIR/intermediate/raw/raw_or_endpoints.json`.
4. Fetch [models.dev](https://models.dev) `api.json` (or reuse a ≤24h cache under
   `DATA_DIR/cache/models_dev/`) and map the `openrouter` provider’s `open_weights` flags by
   OpenRouter model id. Mirror the payload to `DATA_DIR/intermediate/raw/raw_models_dev.json`.
5. For each distinct non-empty OpenRouter `hugging_face_id`, resolve parameter count from the
   Hugging Face Hub model API (`safetensors.total` → billions as `parameters_b`). Responses are
   cached under `DATA_DIR/cache/hf/` (permanent per repo id; new ids still fetch on cache miss);
   network calls use a project User-Agent, ~1s pacing, and 429 backoff. Optional `HF_TOKEN` raises
   Hub rate limits.
6. Map each remaining model to a `CombinedModel` (`llm_rankings/combined_models.py`): identity,
   modalities, OpenRouter URL, embedded Artificial Analysis indices as `benchmark_or_*`,
   plus `is_open_weights` / `parameters_b` when enrichment succeeds. List-level OR `pricing` is
   **not** copied — model `pricing_*` / `speed_*` stay null until aggregated from providers.
   Nested Design Arena rows are not copied (list of objects, not a single score).
7. Optional (`OR_WEB_ENRICHMENT=1` + `OR_ENRICHMENT_MODEL`): gap-fill remaining null
   `is_open_weights` / `parameters_b` / `knowledge_cutoff` via OpenRouter
   `POST /chat/completions` with the Exa `web` plugin (`llm_rankings/web_enrichment.py`).
   Never overwrites OpenRouter / models.dev / HF values. Durable per-model cache (schema v2)
   and cost ledger/summary under `DATA_DIR/cache/web_enrichment/`.
8. Flatten endpoint providers into `ModelProviderEndpoint` rows (`llm_rankings/provider_endpoints.py`):
   `$/1M` input/output price, optional discount, throughput/latency percentiles (p50–p99),
   status/uptime/quantization/context. Primary key is ``{model_id}|{tag}``.
9. Store both tables in SQLite (`models`, `model_provider_endpoints`).

`DATA_DIR/cache/` survives `erase_data_dir()` so wipe/refresh does not re-hammer upstreams
or re-bill web enrichment for known model ids.

### Refresh cadence (hard 24h cap)

All wipe-and-rebuild entry points go through `llm_rankings.refresh.refresh_if_stale`:

- Skip when `database.db` exists and `DATA_DIR/cache/last_refresh.json` is younger than 24h (no
  force bypass).
- Otherwise wipe SQLite (if present), run the pipeline above (OpenRouter models/endpoints and
  models.dev may be served from disk cache), then write `last_refresh_at`.
- API lifespan calls this on startup and again about every hour via an in-process checker.
- `python -m llm_rankings.database` uses the same gate (no public HTTP refresh endpoint).
