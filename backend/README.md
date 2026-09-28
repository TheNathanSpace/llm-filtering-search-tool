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
- Artificial Analysis: [`../api-docs/openapi-artificialanalysis.yaml`](../api-docs/openapi-artificialanalysis.yaml)
  (from https://artificialanalysis.ai/api/v2/openapi)

- Artificial Analysis:
  - API reference: <https://artificialanalysis.ai/api-reference#models-endpoint>
  - Key endpoint: `GET /data/llms/models`
  - Authentication: `x-api-key: <api-key>` header
- OpenRouter:
  - API reference: <https://openrouter.ai/docs/api/api-reference/models/get-models>
  - Key endpoints: `GET /models`, `GET /benchmarks`
    ([list benchmarks](https://openrouter.ai/docs/api/api-reference/benchmarks/list-benchmarks))
  - Authentication: `Authorization: Bearer <api-key>` header
  - Response shapes: `llm_rankings/or_models.py` (aligned with OpenRouter Models API `Model` /
    `ModelsListResponse` schemas in `api-docs/openapi-openrouter.json`). Architecture
    `input_modalities` / `output_modalities` use the `InputModality` / `OutputModality` enums.
  - This project's FastAPI OpenAPI export (for the front-end client) is written to
    `DATA_DIR/openapi.json` by `bin/generate-openapi-docs.sh` (default `./data/openapi.json`).
  - `GET /benchmarks` is called with no `source` or `max_results` filter so every published row
    from all sources is returned. The raw JSON is written to
    `DATA_DIR/intermediate/raw/benchmarks.json` (rate-limited to 30 requests/minute per key and
    500 requests/day per account).

## Cross-Referencing OpenRouter and Artificial Analysis

1. Split OpenRouter model IDs into provider and model names. Extract providers.
2. Extract providers from each Artificial Analysis model.
3. De-duplicate each list of providers.
4. Pair up OpenRouter and Artificial Analysis providers. Write matched/unmatched providers to
   `DATA_DIR/intermediate/providers.json`.
5. For each provider, check Levenshtein distance between each model combination. Pair up models.
6. Write a global matched/unmatched model summary to `DATA_DIR/intermediate/models.json` (clean
   names; unmatched includes models from unmatched providers and leftovers within matched ones).
7. Combine paired up models into single objects (`CombinedModel` in
   `llm_rankings/combined_models.py`), including OpenRouter `input_modalities` /
   `output_modalities` (`InputModality` / `OutputModality` enums). Artificial Analysis
   evaluation scores are stored as `benchmark_aa_<field>`; OpenRouter Artificial Analysis
   indices are stored as `benchmark_or_<field>`. Nested OpenRouter Design Arena rows are not
   copied (they are a list of objects, not a single score).
8. Store models in SQLite database.

On API startup, if `DATA_DIR/database.db` does not exist, the server runs this pipeline automatically
(`populate_with_models`). Use `POST /refresh` or `python -m llm_rankings.database` to wipe and rebuild later.
