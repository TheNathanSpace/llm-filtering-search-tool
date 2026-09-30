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
| D-01 | Primary data source | **Decided: OpenRouter-only.** Artificial Analysis fetch/match/`AA_API_KEY`/`benchmark_aa_*` removed. |
| D-02 | Benchmark set for “intelligence” UX | **Decided:** use OpenRouter-embedded AA indices: `benchmark_or_intelligence_index`, `benchmark_or_coding_index`, `benchmark_or_agentic_index` (general / coding / agentic). No dedicated “reasoning” index on OR yet — treat intelligence as the general proxy unless a later source appears. |
| D-03 | OpenRouter `GET /benchmarks` | **Decided: do not fetch.** Unused raw dump removed. Intelligence scores come from embedded `OpenRouterModel.benchmarks.artificial_analysis` only. |

---

## Active backlog (priority order)

### 1. Core filter/sort dimensions (README motivation)

Ship dedicated filters (and grid columns where missing) for the five dimensions users care about:

| Item | Requirement | Current gap |
| --- | --- | --- |
| Intelligence filter + column + default sort | [QRY-01](requirements.md#qry-01) | **Done** (columns, default sort, panel range filters for intelligence / coding / agentic). |
| Price filter | [QRY-02](requirements.md#qry-02) | **Done.** Model prices are the chosen provider’s listed $/1M (90% input / 10% output). |
| Throughput source + filter | [QRY-03](requirements.md#qry-03) | **Done.** Panel range on the chosen provider’s p50 tokens/s. Provider multi-select and latency range ship with it. |
| Context window filter | [QRY-04](requirements.md#qry-04) | **Done** (range filter + column). |
| Release / creation date filter | [QRY-05](requirements.md#qry-05) | **Done** (creation-date range filter + column). |
| Open weights filter + column | [QRY-11](requirements.md#qry-11), [UI-09](requirements.md#ui-09) | **Done** (models.dev enrichment + switch + column; opt-in Exa gap-fill [SRC-12](requirements.md#src-12)). |
| Parameter size filter + column | [QRY-12](requirements.md#qry-12), [UI-09](requirements.md#ui-09) | **Done** (HF Hub via `hugging_face_id`; range filter + `7B`-style column; opt-in Exa gap-fill when HF missing). |
| Name / family search | [QRY-13](requirements.md#qry-13) | **Done** (panel substring search). |

Related UX: always-visible range controls for shipped numeric filters (**done**), including price, throughput, and latency for the chosen provider.

### 2. Plots

| Item | Requirement | Notes |
| --- | --- | --- |
| User-driven plots | [UI-02](requirements.md#ui-02) | README goal #3; **not started**. |

### 3. Docs / process hygiene

| Item | Notes |
| --- | --- |
| Root `todo.md` redirect | **Done** — pointer to this file. |
| Keep this backlog authoritative | Ongoing — delete or redirect stray lists when found (none found this pass). |
| Refresh `api-docs/` when implementing against upstream APIs | Ongoing — `./bin/update-external-api-docs.sh` (OpenRouter only). |

---

## Done (recently consolidated away)

- Usage cost column (UI-11): filter-panel token count in millions; column left of pricing input uses the 90/10 listed blend
- OpenRouter Exa web gap-fill (SRC-12): open-weights, size, and knowledge cutoff; cache + cost ledger
- OpenRouter per-provider endpoints ingest (SRC-10): pricing + throughput/latency table
- Agent private-worktree lifecycle: `.cursor/worktrees.json` setup (incl. `HOST_DATA_DIR` → primary `data/`); feature-branch rule isolates edits, Compose preview on ask, merges to primary `main` only with go-ahead, then stops preview + deletes worktree + branch; README pointer
- Docs accuracy pass: drop finished “always-visible ranges” / intelligence-filter backlog wording; collapse finished benchmarks section
- Benchmarks data path (D-01–D-03): map `benchmark_or_*` to UI; OpenRouter-only AA removal; drop unused `GET /benchmarks` dump. Stretch later only if Design Arena / OR-native evals are wanted
- Drop `typesafe/jev-router` / floating `*-latest` aliases (e.g. `openai/gpt-chat-latest`) at combine time
- Drop OpenRouter `openrouter/*` meta routers/tools at combine time
- Drop OpenRouter `:batch` variants at combine time (alongside `~` / `:free`)
- Drop OpenRouter `:free` variants at combine time (alongside `~` provider listings)
- Drop OpenRouter `~` provider listings at combine time; remove unused OR/util helpers
- Price output/input range filters (QRY-02)
- Name / family panel text search (QRY-13)
- Open weights + size: models.dev + Hugging Face enrichment, columns, filter panel (QRY-11/12, SRC-09, UI-09)
- OpenRouter-only data path: dropped Artificial Analysis fetch/match, `AA_API_KEY`, and AA UI/fields; intelligence from embedded OR AA indices
- External OpenAPI vendoring + refresh script (`api-docs/`, `bin/update-external-api-docs.sh`)
- Docker Compose is the app run path (`prod` default + `dev` hot-reload profile); removed host `start-*-live.sh` scripts
- Docker compose aligned with app ports/healthcheck
- Agent guidance lives in `.cursor/rules/` (no root `AGENTS.md`)
- Context length + creation date filters
