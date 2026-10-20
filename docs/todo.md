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
| D-02 | Benchmark set for “intelligence” UX | **Decided:** use OpenRouter-embedded AA indices: `benchmark_or_intelligence_index`, `benchmark_or_coding_index`, `benchmark_or_agentic_index` (general / coding / agentic). No dedicated “reasoning” index on OR yet — treat intelligence as the general proxy unless a later source appears. |
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
