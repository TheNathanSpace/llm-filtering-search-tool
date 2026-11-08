# Backlog

> [!IMPORTANT]
> Single ordered list. Do not keep parallel lists in root `todo.md`, the README, or ad-hoc notes. Update this file.

Product goals: [`requirements.md`](requirements.md).
What ships: [`status.md`](status.md).

## Open decisions

Record a choice in this table when it is made.

| ID | Decision | Options / notes |
| --- | --- | --- |
| D-01 | Primary data source | **Decided: OpenRouter-only.** Artificial Analysis fetch/match/`AA_API_KEY`/`benchmark_aa_*` removed. |
| D-02 | Benchmark set for “intelligence” UX | **Decided:** Intelligence is the OpenRouter Artificial Analysis index (`benchmark_or_intelligence_index`). Coding (`benchmark_coding`) is 60% FrontierCode 2.0 and 40% Terminal-Bench 4.0 from the effort whose intelligence index matches that catalog value. Agentic is not a column. |
| D-03 | OpenRouter `GET /benchmarks` | **Decided: do not fetch.** Unused raw dump removed. Intelligence scores come from embedded `OpenRouterModel.benchmarks.artificial_analysis` only. |

## Active backlog

### 1. Plots

| Item | Requirement | Notes |
| --- | --- | --- |
| User-driven plots | [UI-02](requirements.md#ui-02) | Not started |

### 2. Docs / process hygiene

| Item | Notes |
| --- | --- |
| Keep this backlog authoritative | Delete or redirect stray lists when found |
| Refresh `api-docs/` when implementing against upstream APIs | `./bin/update-external-api-docs.sh` (OpenRouter only) |

Shipped items: Status column in [`requirements.md`](requirements.md).
