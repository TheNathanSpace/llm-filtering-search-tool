# Requirements

Product source of truth. Implement and track work against these IDs.  
Ordered engineering backlog: [`todo.md`](todo.md). Snapshot of what ships today: [`status.md`](status.md).

Status values: **must** (needed for the core product), **stretch**, **done** (meets the requirement in the current app), **partial** / **stub** / **open** where noted.

---

## Goals

Help a user pick an LLM by filtering and sorting on the dimensions that matter for their situation, using up-to-date external metadata.

---

## Query / filter dimensions

Core five from the product motivation, plus filters already shipped beyond that set.

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="qry-01"></a>QRY-01 | Filter and sort by **intelligence** (OpenRouter AA indices per [todo D-02](todo.md#open-decisions)) | must | done — Intelligence / Coding / Agentic columns, default intelligence sort, and panel range filters |
| <a id="qry-02"></a>QRY-02 | Filter and sort by **price** (prefer $/1M output tokens; input optional) | must | done — model `pricing_*` are the chosen provider’s listed $/1M (90/10 input/output blend; see [SRC-06](requirements.md#src-06)) |
| <a id="qry-03"></a>QRY-03 | Filter and sort by **throughput** (tokens/second) | must | done — column and panel range use the chosen provider’s p50 tokens/s |
| <a id="qry-04"></a>QRY-04 | Filter and sort by **context window** | must | done |
| <a id="qry-05"></a>QRY-05 | Filter and sort by **release / creation date** | must | done |
| <a id="qry-06"></a>QRY-06 | Filter by **creator** (multi-select from data-derived options) | must | done — options and the column use the catalog display name (`OpenAI`), not the lowercase author slug |
| <a id="qry-07"></a>QRY-07 | Filter by **knowledge cutoff** date range | must | done |
| <a id="qry-08"></a>QRY-08 | Filter by **input modalities** (model must include every checked type) | must | done |
| <a id="qry-09"></a>QRY-09 | Filter by **output modalities** (model must include every checked type) | must | done |
| <a id="qry-10"></a>QRY-10 | Option to treat **missing values as included** when filters would otherwise drop them | must | done |
| <a id="qry-11"></a>QRY-11 | Filter and sort by **open weights** (boolean from models.dev) | must | done |
| <a id="qry-12"></a>QRY-12 | Filter and sort by **parameter size** (billions; display as e.g. `7B`) | must | done |
| <a id="qry-13"></a>QRY-13 | Filter by **name** (case-insensitive substring; finds names/families) | must | done — panel text search |

---

## Data sources and pipeline

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="src-01"></a>SRC-01 | Ingest model metadata from configured upstream APIs into SQLite | must | done (OpenRouter only; skip `~`, `:free` / `:batch`, `openrouter/*`, `*-router`, floating `*-latest`) |
| <a id="src-02"></a>SRC-02 | Wipe and rebuild local data when stale (hard 24h cap on auto/default CLI) via auto-refresh and CLI — no public HTTP refresh endpoint. Ops may `--force` (selective cache bust + rebuild) via `python -m llm_rankings.refresh` / `./bin/refresh-data.sh` | must | done (API startup + hourly checker; gated CLI; ops `--force` with `--source`) |
| <a id="src-03"></a>SRC-03 | Prefer a single coherent benchmark story for intelligence UX | must | done — OpenRouter-embedded AA indices (`benchmark_or_*`) |
| <a id="src-04"></a>SRC-04 | ~~Match OpenRouter and Artificial Analysis providers/models~~ | — | dropped — OpenRouter-only ([todo D-01](todo.md#open-decisions)) |
| <a id="src-05"></a>SRC-05 | **Auto-refresh** SQLite on API startup when the DB is missing or last successful refresh is ≥24h old | must | done |
| <a id="src-06"></a>SRC-06 | Persist a **combined model** record (identity, modalities, OpenRouter URL, OR AA indices as `benchmark_or_*`; chosen-provider listed `pricing_*`, `selected_provider`, p50 `throughput` / `latency_ms`; open-weights + size when enrichment succeeds); exclude OpenRouter `~`, `:free` / `:batch`, `openrouter/*`, `*-router`, and floating `*-latest` | must | done |
| <a id="src-07"></a>SRC-07 | ~~Fetch OpenRouter `GET /benchmarks` and store the raw response~~ | — | dropped — unused dump removed ([todo D-03](todo.md#open-decisions)) |
| <a id="src-08"></a>SRC-08 | Write raw upstream model payloads under `DATA_DIR/intermediate/raw/` for debugging | stretch | done |
| <a id="src-09"></a>SRC-09 | Enrich models with **open weights** (models.dev) and **parameter size** (Hugging Face Hub via `hugging_face_id`), with durable disk cache and polite rate limits | must | done |
| <a id="src-10"></a>SRC-10 | Fetch OpenRouter `GET /models/{author}/{slug}/endpoints` per catalog model (polite concurrency + 429 backoff); persist per-provider **pricing + throughput/latency** rows (`model_provider_endpoints`) | must | done |
| <a id="src-11"></a>SRC-11 | Hit upstream model APIs **at most once per 24h** on automatic/default paths: OpenRouter models + endpoints + models.dev ≤24h disk caches; HF durable per-repo cache; in-process hourly checker calls the same hard-capped refresh gate; rebuild SQLite via normal populate (cache hits when fresh). Ops `--force` may invalidate selected caches and rebuild immediately | must | done |
| <a id="src-12"></a>SRC-12 | Opt-in **web gap-fill** for missing `is_open_weights` / `parameters_b` / `knowledge_cutoff` via OpenRouter chat + Exa (`OR_WEB_ENRICHMENT`, `OR_ENRICHMENT_MODEL`); never overwrite OR/models.dev/HF; durable cache + local cost ledger under `DATA_DIR/cache/web_enrichment/` | stretch | done |

---

## UI

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="ui-01"></a>UI-01 | Browse models in a filterable, sortable table (MUI Data Grid) | must | done |
| <a id="ui-02"></a>UI-02 | Generate plots from user-selected metrics/models | stretch | not started |
| <a id="ui-03"></a>UI-03 | Dedicated **filter panel** with shared range/multi/checkbox/text controls (not only grid column menus) | must | done — covers QRY-01–QRY-13 plus chosen-provider, throughput, and latency ranges; numeric endpoints can be typed; date ranges stay sliders; controls flow into two columns of similar height; column-backed filters follow the table column order |
| <a id="ui-04"></a>UI-04 | Show **identity/metadata** columns: name, open weights, size, context length, created, knowledge cutoff, creator | must | done — description and modality columns are omitted; modalities stay as panel filters |
| <a id="ui-05"></a>UI-05 | Show **outbound links** to OpenRouter model pages | must | done — the name cell is the link; there is no separate URL column |
| <a id="ui-06"></a>UI-06 | Show **pricing and speed** for one provider: listed input/output price, median tokens/s, median time-to-first-token | must | done — those columns plus panel filters, including a provider multi-select; the provider name is not a table column; provider chosen by 90/10 listed blend, unless the next provider is much faster on both median latency and throughput |
| <a id="ui-07"></a>UI-07 | Load models from the API via a **generated TypeScript client** (same-origin `/api`) | must | done |
| <a id="ui-08"></a>UI-08 | Landing header with product title, short goal copy, and GitHub link | stretch | done |
| <a id="ui-09"></a>UI-09 | Show **open weights** and **size** columns; dedicated open-weights switch and size range filter in the filter panel | must | done |
| <a id="ui-10"></a>UI-10 | Bottom-left footer row: **last data refresh** and lifetime **enrichment research cost** (browser local date/time; UTC tooltip on hover) | stretch | done |

---

## Platform and operations

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="plt-01"></a>PLT-01 | REST API for health, model list, and metadata (`GET /health`, `GET /models`, `GET /meta`) | must | done — `/meta` returns `{enrichment_cost_usd, last_refresh_at}`; data refresh is automatic / CLI (incl. ops `--force`); no public HTTP refresh ([SRC-02](#src-02), [SRC-11](#src-11)); interactive API docs off unless `ENABLE_API_DOCS`; 500 responses use a generic client message |
| <a id="plt-02"></a>PLT-02 | Docker Compose run paths documented in README (`prod` default, `dev` hot-reload profile); worktree preview reuses primary `data/` via `HOST_DATA_DIR` | must | done |
| <a id="plt-03"></a>PLT-03 | Shared **`.env` configuration** (`OR_API_KEY`, optional `HF_TOKEN`, optional `OR_WEB_ENRICHMENT` / `OR_ENRICHMENT_MODEL`, optional `ENABLE_API_DOCS`, `DATA_DIR`, optional `HOST_DATA_DIR` for worktree Compose mounts, logging, host/ports) | must | done |
| <a id="plt-04"></a>PLT-04 | **Logging** to stdout and rotating files under `DATA_DIR/logs/` (with `latest.log`); front-end server logs can append to the same file | must | done |
| <a id="plt-05"></a>PLT-05 | Front-end **proxies** `/api/*` to the back-end using runtime `BACKEND_HOST` / `BACKEND_PORT` | must | done |
| <a id="plt-06"></a>PLT-06 | **Docker** Compose: `prod` image runs API + Next via supervisord; `dev` profile runs separate reloadable backend/frontend services; UI port published; API health-checked | must | done |
| <a id="plt-07"></a>PLT-07 | Regenerate this project's FastAPI OpenAPI → TypeScript client (`bin/install-frontend-api-client.sh`) | must | done |
| <a id="plt-08"></a>PLT-08 | Vendor upstream OpenAPI specs under `api-docs/` and refresh via script | stretch | done |

---

## Information architecture

```text
OpenRouter (+ endpoints) + models.dev + HF (+ opt-in OR chat/Exa gap-fill) → retrieve/clean/enrich → SQLite
  tables: models (CombinedModel), model_provider_endpoints (per-provider price/speed)
                                                                      ↓
                                                                FastAPI /models
                                                                      ↓
                                               Next.js /api proxy → generated client
                                                                      ↓
                                                         filter panel + Data Grid
                                                                      ↓
                                                               (stretch) plots
```

Upstream OpenAPI references: [`../api-docs/`](../api-docs/).
