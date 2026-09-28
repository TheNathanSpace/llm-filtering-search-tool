# Status

**Last updated:** 2026-09-28 — Daily API refresh hard cap  
**Latest change:** Enforce at-most-once-per-day upstream fetches: OpenRouter 24h disk cache, shared freshness gate, startup + hourly auto-refresh, hard-capped `POST /refresh` / CLI ([SRC-10](requirements.md#src-10)).

## Pickup

| Area | State |
| --- | --- |
| Data fetch (OR + models.dev + HF) | Implemented ([SRC-01](requirements.md#src-01), [SRC-05](requirements.md#src-05)–[SRC-06](requirements.md#src-06), [SRC-09](requirements.md#src-09)–[SRC-10](requirements.md#src-10)) |
| SQLite + FastAPI | Implemented ([PLT-01](requirements.md#plt-01), [SRC-02](requirements.md#src-02), [SRC-05](requirements.md#src-05), [SRC-10](requirements.md#src-10)) |
| Next.js table + filters | [QRY-01](requirements.md#qry-01)–[QRY-02](requirements.md#qry-02), [QRY-04](requirements.md#qry-04)–[QRY-13](requirements.md#qry-13) + [UI-04](requirements.md#ui-04)–[UI-06](requirements.md#ui-06), [UI-09](requirements.md#ui-09); throughput filter still open ([todo §1](todo.md#1-core-filtersort-dimensions-readme-motivation)) |
| Plots | Not started ([UI-02](requirements.md#ui-02)) |
| Docker / env / logging / proxy | [PLT-02](requirements.md#plt-02)–[PLT-06](requirements.md#plt-06) |
| External + project OpenAPI tooling | [PLT-07](requirements.md#plt-07), [PLT-08](requirements.md#plt-08) |
| Requirements + backlog | [`requirements.md`](requirements.md), [`todo.md`](todo.md) |

## UI map (filters vs columns)

| Dimension | Column | Dedicated filter | Requirement |
| --- | --- | --- | --- |
| Name | yes | yes (substring search) | [QRY-13](requirements.md#qry-13) |
| Intelligence | yes (Intelligence / Coding / Agentic) | yes (three range filters) | [QRY-01](requirements.md#qry-01) |
| Price | yes | yes (output + input $/1M ranges) | [QRY-02](requirements.md#qry-02), [UI-06](requirements.md#ui-06) |
| Throughput | yes (always empty) | no | [QRY-03](requirements.md#qry-03), [UI-06](requirements.md#ui-06) — source TBD |
| Context length | yes | yes | [QRY-04](requirements.md#qry-04) |
| Creation date | yes | yes | [QRY-05](requirements.md#qry-05) |
| Creator | yes | yes | [QRY-06](requirements.md#qry-06) |
| Knowledge cutoff | yes | yes | [QRY-07](requirements.md#qry-07) |
| Input / output modalities | yes | yes | [QRY-08](requirements.md#qry-08), [QRY-09](requirements.md#qry-09) |
| Open weights | yes | yes (switch) | [QRY-11](requirements.md#qry-11), [UI-09](requirements.md#ui-09) |
| Size (B params) | yes | yes (range) | [QRY-12](requirements.md#qry-12), [UI-09](requirements.md#ui-09) |

## Next session

Start from **[`todo.md`](todo.md)** (throughput source, then filter). Do not resurrect parallel lists.
