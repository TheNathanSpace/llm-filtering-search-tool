# Backlog

Single ordered todo list for this project. Do not keep parallel lists in root `todo.md`,
README “next ideas”, or ad-hoc notes — update **this file** instead.

Product goals and requirement IDs: [`requirements.md`](requirements.md).  
Current implementation snapshot: [`status.md`](status.md).

---

## Open decisions

Resolve these before large data-model refactors. Record the choice here when made.

| ID | Decision | Options / notes |
| --- | --- | --- |
| D-01 | Primary data source | **Today:** Artificial Analysis + OpenRouter matched into `CombinedModel`. **Lean:** OpenRouter-only (see root scratch notes historically). If OR-only, drop AA fetch/match/`AA_API_KEY` and AA-prefixed fields. |
| D-02 | Benchmark set for “intelligence” UX | Need one focused score (or small set) each for: **general intelligence**, **agentic tasks**, **reasoning**, **coding**. Candidates already on models: `benchmark_or_intelligence_index`, `benchmark_or_coding_index`, `benchmark_or_agentic_index`, plus many `benchmark_aa_*`. Prefer OR indices if D-01 is OR-first. |
| D-03 | OpenRouter `GET /benchmarks` | **Today:** fetched and written to `DATA_DIR/intermediate/raw/benchmarks.json`, **not** joined into SQLite/UI. Either wire it into the combine pipeline (and Pydantic models for that payload) or stop fetching it. Model-embedded `OpenRouterModel.benchmarks` is already parsed. |

---

## Active backlog (priority order)

### 1. Core filter/sort dimensions (README motivation)

Ship dedicated filters (and grid columns where missing) for the five dimensions users care about:

| Item | Requirement | Current gap |
| --- | --- | --- |
| Intelligence filter + column + default sort | [QRY-01](requirements.md#qry-01) | Scores exist on API (`benchmark_or_*` / `benchmark_aa_*`); **not** in Data Grid or filter panel. Blocked on **D-02** (which field(s)). |
| Price filter | [QRY-02](requirements.md#qry-02) | `pricing_input` / `pricing_output` columns exist; **no** dedicated min/max filter (grid column filters only). |
| Throughput filter | [QRY-03](requirements.md#qry-03) | `speed_tokens_per_second` column exists; **no** dedicated filter. |
| Context window filter | [QRY-04](requirements.md#qry-04) | **Done** (range filter + column). |
| Release / creation date filter | [QRY-05](requirements.md#qry-05) | **Done** (creation-date range filter + column). |

Related UX: always-visible range controls for price (and other numeric filters) rather than relying on Data Grid column menus alone.

### 2. Benchmarks data path (AA replacement / OR expansion)

Depends on **D-01**–**D-03**. Consolidated former root `todo.md` items:

1. If keeping/enriching OpenRouter benchmarks: model and ingest whatever **D-03** chooses (`GET /benchmarks` and/or expand use of embedded `benchmarks`).
2. Map **D-02** choices onto `CombinedModel` fields exposed to the UI.
3. If **D-01** is OpenRouter-only: remove AA retrieve/match/models, `benchmark_aa_*`, Artificial Analysis URLs/columns, and `AA_API_KEY` from config/docs.
4. If keeping AA temporarily: treat AA scores as backup only; do not block intelligence UX on AA-only fields.

### 3. Plots

| Item | Requirement | Notes |
| --- | --- | --- |
| User-driven plots | [UI-02](requirements.md#ui-02) | README goal #3; **not started**. Stretch until filter/sort dimensions work. |

### 4. Docs / process hygiene

| Item | Notes |
| --- | --- |
| Keep this backlog authoritative | Delete or redirect stray todo lists when found. |
| Refresh `api-docs/` when implementing against upstream APIs | `./bin/update-external-api-docs.sh` |

---

## Done (recently consolidated away)

- External OpenAPI vendoring + refresh script (`api-docs/`, `bin/update-external-api-docs.sh`)
- Docker compose aligned with app ports/healthcheck
- Agent guidance moved to `.cursor/rules/` (root `AGENTS.md` is a pointer)
- Context length + creation date filters
