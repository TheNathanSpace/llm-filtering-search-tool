# Status

**Last updated:** 2026-09-28 — Merged OpenRouter-only to main  
**Latest change:** Locally merged `feature/openrouter-only` into `main` (OR-only ingest, intelligence columns/filters, dropped unused `/benchmarks` dump).

## Pickup

| Area | State |
| --- | --- |
| Data fetch (OR models) | Implemented ([SRC-01](requirements.md#src-01), [SRC-05](requirements.md#src-05)–[SRC-06](requirements.md#src-06)) |
| SQLite + FastAPI | Implemented ([PLT-01](requirements.md#plt-01), [SRC-02](requirements.md#src-02), [SRC-05](requirements.md#src-05)) |
| Next.js table + filters | [QRY-01](requirements.md#qry-01), [QRY-04](requirements.md#qry-04)–[QRY-10](requirements.md#qry-10) + [UI-04](requirements.md#ui-04)–[UI-06](requirements.md#ui-06); price/throughput filters still open ([todo §1](todo.md#1-core-filtersort-dimensions-readme-motivation)) |
| Plots | Not started ([UI-02](requirements.md#ui-02)) |
| Docker / env / logging / proxy | [PLT-02](requirements.md#plt-02)–[PLT-06](requirements.md#plt-06) |
| External + project OpenAPI tooling | [PLT-07](requirements.md#plt-07), [PLT-08](requirements.md#plt-08) |
| Requirements + backlog | [`requirements.md`](requirements.md), [`todo.md`](todo.md) |

## UI map (filters vs columns)

| Dimension | Column | Dedicated filter | Requirement |
| --- | --- | --- | --- |
| Intelligence | yes (Intelligence / Coding / Agentic) | yes (three range filters) | [QRY-01](requirements.md#qry-01) |
| Price | yes | no | [QRY-02](requirements.md#qry-02), [UI-06](requirements.md#ui-06) |
| Throughput | yes (always empty) | no | [QRY-03](requirements.md#qry-03), [UI-06](requirements.md#ui-06) — source TBD |
| Context length | yes | yes | [QRY-04](requirements.md#qry-04) |
| Creation date | yes | yes | [QRY-05](requirements.md#qry-05) |
| Creator | yes | yes | [QRY-06](requirements.md#qry-06) |
| Knowledge cutoff | yes | yes | [QRY-07](requirements.md#qry-07) |
| Input / output modalities | yes | yes | [QRY-08](requirements.md#qry-08), [QRY-09](requirements.md#qry-09) |

## Next session

Start from **[`todo.md`](todo.md)** (price filter, then throughput source). Do not resurrect parallel lists.
