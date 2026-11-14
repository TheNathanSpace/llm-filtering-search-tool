# Status

**Last updated:** 2026-11-13 — Latency tooltip includes ms
**Latest change:** Latency hover text is the millisecond count with commas and an `ms` suffix (`4,180 ms`), on the table cell and the filter slider.

## Pickup

| Area | State |
| --- | --- |
| Data fetch (OR + models.dev + HF + opt-in batch web) | Implemented ([SRC-01](requirements.md#src-01), [SRC-05](requirements.md#src-05)–[SRC-06](requirements.md#src-06), [SRC-09](requirements.md#src-09)–[SRC-12](requirements.md#src-12)) |
| SQLite + FastAPI | Implemented ([PLT-01](requirements.md#plt-01), [PLT-10](requirements.md#plt-10), [SRC-02](requirements.md#src-02), [SRC-05](requirements.md#src-05), [SRC-11](requirements.md#src-11)) |
| Next.js table + filters | Implemented ([QRY-01](requirements.md#qry-01)–[QRY-13](requirements.md#qry-13), [UI-01](requirements.md#ui-01), [UI-03](requirements.md#ui-03)–[UI-06](requirements.md#ui-06), [UI-09](requirements.md#ui-09)–[UI-15](requirements.md#ui-15)) |
| Plots | Not started ([UI-02](requirements.md#ui-02)) |
| Docker / env / logging / proxy | Implemented ([PLT-02](requirements.md#plt-02)–[PLT-06](requirements.md#plt-06), [PLT-09](requirements.md#plt-09)) |
| External + project OpenAPI tooling | Implemented ([PLT-07](requirements.md#plt-07), [PLT-08](requirements.md#plt-08)) |
| Requirements + backlog | [`requirements.md`](requirements.md), [`todo.md`](todo.md) |

## UI map (filters vs columns)

Reset all of these dang modifiers is first in the left column. Pin all filtered models and Clear pins share the next row, each half that column. The missing-values switch follows. Off drops a model missing a value only when that filter is narrowed, selected, or filled in. A full-span range is not active. With no active filters, off changes nothing. A ? beside the switch states this. Panel filters follow this column order. The missing-values switch stays first. Modality filters have no column, so they stay after the column-aligned controls.

| Dimension | Column | Dedicated filter | Requirement |
| --- | --- | --- | --- |
| Pin | yes (pin control; not sortable) | yes (hide unpinned; Pin all filtered models adds the current rows; Clear pins empties the set). Pins stay in the table through other filters, and stay first unless a non-default sort is active | [UI-14](requirements.md#ui-14) |
| Name | yes (links to the OpenRouter page) | yes (name/slug search; punctuation ignored; whole numbers; comma OR; `-` exclude; resizable field) | [QRY-13](requirements.md#qry-13), [UI-05](requirements.md#ui-05) |
| Open weights | yes | yes (switch) | [QRY-11](requirements.md#qry-11), [UI-09](requirements.md#ui-09) |
| Size | yes (thousands through 900k, e.g. `400k`; millions through 900M, e.g. `500M`; billions through 900B, e.g. `410B`; trillions above that, e.g. `1T`; 100–900 of a unit rounds to the nearest 10; tooltip is the parameter count) | yes (range) | [QRY-12](requirements.md#qry-12), [UI-09](requirements.md#ui-09) |
| Intelligence | yes (Intelligence / Coding). Coding is 60% FrontierCode 2.0 and 40% Terminal-Bench 4.0. The header tooltip states that blend. A Coding cell hover shows `FrontierCode 2.0 / Terminal-Bench 4.0: <frontier> / <terminal>` when both inputs are stored. Intelligence is the single OpenRouter index | yes (two range filters) | [QRY-01](requirements.md#qry-01) |
| Context length | yes (thousands through 900k, e.g. `130k`; millions above that, e.g. `1M`; 100–900 of a unit rounds to the nearest 10; tooltip is the token count) | yes | [QRY-04](requirements.md#qry-04) |
| Usage cost | yes, when a positive token count is entered (left of input cost; cell is cents; hover is the full fractional dollars) | token-count box, then a cost range (labels are cents; thumb and endpoint hover is the full fractional dollars) | [UI-11](requirements.md#ui-11) |
| Input / output cost | yes (chosen provider; header tooltip: per million tokens) | yes | [QRY-02](requirements.md#qry-02), [UI-06](requirements.md#ui-06) |
| Throughput | yes (chosen provider p50, last 30 minutes) | yes | [QRY-03](requirements.md#qry-03), [UI-06](requirements.md#ui-06) |
| Latency | yes (chosen provider p50, seconds, last 30 minutes; tooltip is milliseconds, e.g. `4,180 ms`) | yes | [UI-06](requirements.md#ui-06) |
| Creation date | yes | yes | [QRY-05](requirements.md#qry-05) |
| Knowledge cutoff | yes | yes | [QRY-07](requirements.md#qry-07) |
| Creator | yes (`Author:` prefix, else a leading word that starts the slug, else the title-cased slug) | yes | [QRY-06](requirements.md#qry-06) |
| Input / output modalities | no | yes | [QRY-08](requirements.md#qry-08), [QRY-09](requirements.md#qry-09) |

## Next session

Start from **[`todo.md`](todo.md)** (plots). Do not resurrect parallel lists.
