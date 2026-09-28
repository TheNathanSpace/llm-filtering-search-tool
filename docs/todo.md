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
| Price filter | [QRY-02](requirements.md#qry-02) | **Done** (output + input $/1M range filters in the panel). |
| Throughput source + filter | [QRY-03](requirements.md#qry-03) | `speed_*` always null after AA removal. Wire an OpenRouter (or other) throughput source, then add a dedicated filter. |
| Context window filter | [QRY-04](requirements.md#qry-04) | **Done** (range filter + column). |
| Release / creation date filter | [QRY-05](requirements.md#qry-05) | **Done** (creation-date range filter + column). |
| Open weights filter + column | [QRY-11](requirements.md#qry-11), [UI-09](requirements.md#ui-09) | **Done** (models.dev enrichment + switch + column). |
| Parameter size filter + column | [QRY-12](requirements.md#qry-12), [UI-09](requirements.md#ui-09) | **Done** (HF Hub via `hugging_face_id`; range filter + `7B`-style column). |

Related UX: always-visible range controls for shipped numeric filters (**done**). Throughput panel ranges wait on the source above.

### 2. Plots

| Item | Requirement | Notes |
| --- | --- | --- |
| User-driven plots | [UI-02](requirements.md#ui-02) | README goal #3; **not started**. Stretch until filter/sort dimensions work. |

### 3. Docs / process hygiene

| Item | Notes |
| --- | --- |
| Root `todo.md` redirect | **Done** — pointer to this file. |
| Keep this backlog authoritative | Ongoing — delete or redirect stray lists when found (none found this pass). |
| Refresh `api-docs/` when implementing against upstream APIs | Ongoing — `./bin/update-external-api-docs.sh` (OpenRouter only). |

---

## Done (recently consolidated away)

- Agent private-worktree lifecycle: `.cursor/worktrees.json` setup; feature-branch rule isolates edits, merges to primary `main` only with go-ahead, then deletes worktree + branch; README pointer
- Docs accuracy pass: drop finished “always-visible ranges” / intelligence-filter backlog wording; collapse finished benchmarks section
- Benchmarks data path (D-01–D-03): map `benchmark_or_*` to UI; OpenRouter-only AA removal; drop unused `GET /benchmarks` dump. Stretch later only if Design Arena / OR-native evals are wanted
- Drop OpenRouter `~` provider listings at combine time; remove unused OR/util helpers
- Price output/input range filters (QRY-02)
- Open weights + size: models.dev + Hugging Face enrichment, columns, filter panel (QRY-11/12, SRC-09, UI-09)
- OpenRouter-only data path: dropped Artificial Analysis fetch/match, `AA_API_KEY`, and AA UI/fields; intelligence from embedded OR AA indices
- External OpenAPI vendoring + refresh script (`api-docs/`, `bin/update-external-api-docs.sh`)
- Docker compose aligned with app ports/healthcheck
- Agent guidance lives in `.cursor/rules/` (no root `AGENTS.md`)
- Context length + creation date filters
