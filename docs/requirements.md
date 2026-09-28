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
| <a id="qry-02"></a>QRY-02 | Filter and sort by **price** (prefer $/1M output tokens; input optional) | must | done — panel range filters for output and input $/1M; columns already present |
| <a id="qry-03"></a>QRY-03 | Filter and sort by **throughput** (tokens/second) | must | stub — `speed_*` columns exist but are always null pending an OpenRouter (or other) source |
| <a id="qry-04"></a>QRY-04 | Filter and sort by **context window** | must | done |
| <a id="qry-05"></a>QRY-05 | Filter and sort by **release / creation date** | must | done |
| <a id="qry-06"></a>QRY-06 | Filter by **creator** (multi-select from data-derived options) | must | done |
| <a id="qry-07"></a>QRY-07 | Filter by **knowledge cutoff** date range | must | done |
| <a id="qry-08"></a>QRY-08 | Filter by **input modalities** (model must include every checked type) | must | done |
| <a id="qry-09"></a>QRY-09 | Filter by **output modalities** (model must include every checked type) | must | done |
| <a id="qry-10"></a>QRY-10 | Option to treat **missing values as included** when filters would otherwise drop them | must | done |
| <a id="qry-11"></a>QRY-11 | Filter and sort by **open weights** (boolean from models.dev) | must | done |
| <a id="qry-12"></a>QRY-12 | Filter and sort by **parameter size** (billions; display as e.g. `7B`) | must | done |

---

## Data sources and pipeline

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="src-01"></a>SRC-01 | Ingest model metadata from configured upstream APIs into SQLite | must | done (OpenRouter only; skip provider ids starting with `~`) |
| <a id="src-02"></a>SRC-02 | Expose refresh path to wipe and rebuild local data | must | done (`POST /refresh`, `python -m llm_rankings.database`) |
| <a id="src-03"></a>SRC-03 | Prefer a single coherent benchmark story for intelligence UX | must | done — OpenRouter-embedded AA indices (`benchmark_or_*`) |
| <a id="src-04"></a>SRC-04 | ~~Match OpenRouter and Artificial Analysis providers/models~~ | — | dropped — OpenRouter-only ([todo D-01](todo.md#open-decisions)) |
| <a id="src-05"></a>SRC-05 | **Auto-seed** SQLite on API startup when `DATA_DIR/database.db` is missing | must | done |
| <a id="src-06"></a>SRC-06 | Persist a **combined model** record (identity, pricing, modalities, OpenRouter URL, OR AA indices as `benchmark_or_*`; `speed_*` reserved/null; open-weights + size when enrichment succeeds); exclude OpenRouter `~` provider listings | must | done |
| <a id="src-07"></a>SRC-07 | ~~Fetch OpenRouter `GET /benchmarks` and store the raw response~~ | — | dropped — unused dump removed ([todo D-03](todo.md#open-decisions)) |
| <a id="src-08"></a>SRC-08 | Write raw upstream model payloads under `DATA_DIR/intermediate/raw/` for debugging | stretch | done |
| <a id="src-09"></a>SRC-09 | Enrich models with **open weights** (models.dev) and **parameter size** (Hugging Face Hub via `hugging_face_id`), with durable disk cache and polite rate limits | must | done |

---

## UI

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="ui-01"></a>UI-01 | Browse models in a filterable, sortable table (MUI Data Grid) | must | done (core QRY filters still incomplete) |
| <a id="ui-02"></a>UI-02 | Generate plots from user-selected metrics/models | stretch | not started |
| <a id="ui-03"></a>UI-03 | Dedicated **filter panel** with shared range/multi/checkbox controls (not only grid column menus) | must | partial — panel covers QRY-01–QRY-02, QRY-04–QRY-12; throughput ranges still missing |
| <a id="ui-04"></a>UI-04 | Show **identity/metadata** columns: name, creator, description, created, knowledge cutoff, context length, input/output modalities, open weights, size | must | done |
| <a id="ui-05"></a>UI-05 | Show **outbound links** to OpenRouter model pages | must | done |
| <a id="ui-06"></a>UI-06 | Show **pricing and latency** columns: input/output price, tokens/s, time-to-first-token, time-to-first-answer-token | must | partial — price columns live; speed columns present but null until a throughput source lands |
| <a id="ui-07"></a>UI-07 | Load models from the API via a **generated TypeScript client** (same-origin `/api`) | must | done |
| <a id="ui-08"></a>UI-08 | Landing header with product title, short goal copy, and GitHub link | stretch | done |
| <a id="ui-09"></a>UI-09 | Show **open weights** and **size** columns; dedicated open-weights switch and size range filter in the filter panel | must | done |

---

## Platform and operations

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| <a id="plt-01"></a>PLT-01 | REST API for health, model list, and data refresh (`GET /health`, `GET /models`, `POST /refresh`) | must | done |
| <a id="plt-02"></a>PLT-02 | Local full-stack and Docker Compose run paths documented in README | must | done |
| <a id="plt-03"></a>PLT-03 | Shared **`.env` configuration** (`OR_API_KEY`, optional `HF_TOKEN`, `DATA_DIR`, logging, host/ports) | must | done |
| <a id="plt-04"></a>PLT-04 | **Logging** to stdout and rotating files under `DATA_DIR/logs/` (with `latest.log`); front-end server logs can append to the same file | must | done |
| <a id="plt-05"></a>PLT-05 | Front-end **proxies** `/api/*` to the back-end using runtime `BACKEND_HOST` / `BACKEND_PORT` | must | done |
| <a id="plt-06"></a>PLT-06 | **Docker** image runs API + Next via supervisord; Compose publishes the UI port and health-checks the API | must | done |
| <a id="plt-07"></a>PLT-07 | Regenerate this project's FastAPI OpenAPI → TypeScript client (`bin/install-frontend-api-client.sh`) | must | done |
| <a id="plt-08"></a>PLT-08 | Vendor upstream OpenAPI specs under `api-docs/` and refresh via script | stretch | done |

---

## Information architecture

```text
OpenRouter + models.dev + Hugging Face → retrieve/clean/enrich → SQLite (CombinedModel)
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
