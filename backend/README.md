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
  - Key endpoint: `GET /models`
  - Authentication: `Authorization: Bearer <api-key>` header
  - Response shapes: `llm_rankings/or_models.py` (aligned with OpenRouter Models API `Model` /
    `ModelsListResponse` schemas in `api-docs/openapi-openrouter.json`). Architecture
    `input_modalities` / `output_modalities` use the `InputModality` / `OutputModality` enums.
    Embedded `benchmarks.artificial_analysis` indices become `benchmark_or_*` on `CombinedModel`.
  - This project's FastAPI OpenAPI export (for the front-end client) is written to
    `DATA_DIR/openapi.json` by `bin/generate-openapi-docs.sh` (default `./data/openapi.json`).

## Building the model table (OpenRouter-only)

1. Fetch OpenRouter `GET /models` and write the raw payload under
   `DATA_DIR/intermediate/raw/raw_or_models.json`.
2. Map each OpenRouter model to a `CombinedModel` (`llm_rankings/combined_models.py`): identity,
   pricing, modalities, OpenRouter URL, and embedded Artificial Analysis indices as
   `benchmark_or_*`. Nested Design Arena rows are not copied (list of objects, not a single score).
3. Throughput / latency fields (`speed_*`) are left null until an OpenRouter (or other) source is
   wired later.
4. Store models in SQLite (`pk` = OpenRouter model `id`).

On API startup, if `DATA_DIR/database.db` does not exist, the server runs this pipeline automatically
(`populate_with_models`). Use `POST /refresh` or `python -m llm_rankings.database` to wipe and rebuild later.
