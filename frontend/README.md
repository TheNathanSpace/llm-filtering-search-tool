# Front-end Docs

- <https://nextjs.org/docs/app/getting-started>
- <https://mui.com/toolpad/core/introduction/>
- <https://mui.com/material-ui/all-components/>
- <https://mui.com/x/react-data-grid/>

Plots: [`docs/todo.md`](../docs/todo.md).

## Logging

On server start, [`instrumentation.ts`](instrumentation.ts) tees Node.js `console.*` and `onRequestError` to `DATA_DIR/logs/latest.log` (the back-end symlink), using `DATA_DIR` and `LOG_LEVEL` from the process environment. Local dev also loads the repo-root `.env`. Browser logs are not written to the file.

> [!WARNING]
> Lines are skipped until `latest.log` exists. Start the API first, or restart the front-end after the API.

## Model filters

Filter UI and logic live under `app/filters/`. Column and filter map: [`docs/status.md`](../docs/status.md).

| Module | Role |
| --- | --- |
| `model-filters.tsx` | Filter panel layout |
| `token-count-field.tsx` | Token-count box for the usage-cost column and range |
| `filter-option.tsx` | Shared label + control row |
| `multi-select-filter.tsx` / `date-range-filter.tsx` / `number-range-filter.tsx` / `text-filter.tsx` | Range, select, and text controls |
| `checkbox-row-filter.tsx` | Checkbox row; label under each box |
| `modality-options.ts` | Input and output modality options |
| `filter-types.ts` | Filter state and bounds types |
| `filter-bounds.ts` | Min/max and unique creators from models |
| `apply-filters.ts` | Pure `filterModels()` |
| `name-query.ts` | Name and slug matching |
| `use-model-filters.ts` | State and filtered rows |
| `filter-query.ts` | Read and write the page query string |
| `use-sync-table-query.ts` | Keep the address bar aligned with that state |

- The panel uses two columns of about the same height. A control is not split across the break.
- **Reset all of these dang filters** is first in the left column, above **Clear pins**, and fills that column. The label uses the filter text size and color; the outline stays blue. It restores default filter choices, including turning hide-unpinned off, and clears the token count. It leaves pinned ids in place. Range sliders remount so the thumbs match those defaults. Table sort stays, except a usage-cost sort, which drops with the token count ([UI-13](../docs/requirements.md#ui-13)).
- **Clear pins** sits under reset and uses the same button. It empties the pin set and turns hide-unpinned off ([UI-14](../docs/requirements.md#ui-14)).
- `model-table.tsx` composes the filter panel and Data Grid. Pagination stays on. Virtualization is off, so every row and column on the current page is in the document and browser find can reach them. Column definitions: `app/columns.tsx`. Cells and column headers do not show a focus outline. The first column is a pin control.
- Column-backed filters follow that column order. The missing-values switch is first, then hide unpinned. Modality filters have no column, so they come after the column-aligned controls.
- **Millions of tokens** sits just before the price ranges. A positive count inserts a **Cost (NM)** column left of Input Cost and a **Cost** range under the box: `tokens × (0.90 × input $/1M + 0.10 × output $/1M)` for the chosen provider. The range keeps models inside it. Missing prices follow the missing-values switch. Changing or clearing the count resets that range. Clearing the count removes the column. The blend matches `backend/llm_rankings/provider_choice.py`. A help icon on the token field and on the Cost range states the count, the column, and the blend.
- The name cell links to the model’s OpenRouter page.
- Name search matches display names and OpenRouter ids and slugs, ignoring punctuation (`gpt 5` matches `GPT-5`). A decimal point between digits stays. A number matches that whole numeric span, including inside a word (`4.1` matches `v4.1`; `5` does not match `5.5` or `15`). Other words stay substring matches. Commas separate OR alternatives. A leading `-` on a comma unit excludes models that match every word in that unit. The field is one line and can be dragged taller. A help icon next to the Name label states the matching rules.
- Creator values use the `Author:` prefix on the model name when it has one. Otherwise they use a leading word that starts the author slug, or the title-cased slug.
- Modality filters keep models that include every checked type. Unchecked means no constraint.
- `NumberRangeFilter`, including size, shows the selected minimum and maximum under the slider. Click either number to type a value. Enter or leaving the field applies it. Clearing the field restores that end to the data bound. Escape cancels. The value stays inside the data bounds. If it crosses the other end, that end moves with it. Latency labels are seconds (`3.11s`); a typed value is seconds, and a trailing `s` is optional. Context labels are thousands under 500,000 tokens (`400k`) and millions from 500,000 (`1.2M`). A typed context value accepts `k`/`K` or `m`/`M`; a bare number is the token count. The query string still stores milliseconds and tokens.
- Date range filters are slider-only.

### Shareable URL

The address bar stores filter choices that differ from the defaults, the token-count text, the table sort, and pinned model ids; opening that URL restores the setup. Defaults (missing values included, open-weights off, hide-unpinned off, full ranges, intelligence descending, no pins) stay off the query string; `sort=none` means unsorted; changing the setup replaces the current history entry, so Back leaves the page.

| Parameter | Value |
| --- | --- |
| `missing=0` | Do not treat missing values as included |
| `openWeights=1` | Open weights only |
| `pinnedOnly=1` | Hide unpinned models |
| `pin` | One parameter per pinned OpenRouter id |
| `name` | Name and slug search text |
| `creator` | One parameter per selected creator |
| `size`, `intelligence`, `coding`, `agentic`, `context`, `cost`, `inputCost`, `outputCost`, `throughput`, `latency` | `min,max` |
| `created`, `cutoff` | `startTimestamp,endTimestamp` (milliseconds) |
| `tokens` | Token-count text |
| `input`, `output` | One parameter per modality |
| `sort` | `alias:asc` or `alias:desc`, comma-separated for several columns. Aliases: `name`, `openWeights`, `size`, `intelligence`, `coding`, `agentic`, `context`, `cost`, `inputCost`, `outputCost`, `throughput`, `latency`, `created`, `cutoff`, `creator` |

Example: `/?name=gpt+5&openWeights=1&intelligence=40,80&creator=OpenAI&sort=throughput:desc`

### Adding a new filter

Reuse `MultiSelectFilter`, `DateRangeFilter`, `NumberRangeFilter`, `TextFilter`, or `CheckboxRowFilter` when the interaction already exists.

1. **`filter-types.ts`** — Add the field to `ModelFiltersState` and `UserFilterChoices` (and to `FilterBounds` when it needs min/max or option lists). Update `createInitialUserChoices` and `resolveFilters`. Defaults: `[]` for multi-select, `""` for text, `undefined` for bounds-backed ranges.
2. **`filter-bounds.ts`** — Compute bounds or options in `getFilterBounds` when they come from the model list.
3. **`apply-filters.ts`** — Apply the field in `filterModels`. Respect `includeMissing` for nullable properties.
4. **`model-filters.tsx`** — Render the control and wire `onChange` (and `value` when controlled) into `setFilters`. Pass `defaultStart` / `defaultEnd` from the resolved filter when the control keeps its own state, so a shared URL shows the restored range.
5. **`filter-query.ts`** — Parse and serialize the field. Omit it when it matches `createInitialUserChoices`.

`model-table.tsx` changes only when the filter depends on something outside the model list. Usage cost does: pass the parsed token count into `useModelFilters`. Pins do too: the pin set lives next to the sort model and is passed into `useModelFilters` and `columnsForTokenMillions`.

## Running

Commands: [root README](../README.md).

The browser calls same-origin `/api/*`. [`proxy.ts`](proxy.ts) rewrites each request to `http://<BACKEND_HOST>:<BACKEND_PORT>`. Compose `dev` sets `BACKEND_HOST=backend`. `0.0.0.0` is mapped to `127.0.0.1` for same-container bind-all. Host and port are read per request, so Compose `environment:` overrides apply without a rebuild.

Optional host `npm` install (lint and API client regen): `../bin/setup-frontend.sh`.

## API client

`../bin/install-frontend-api-client.sh` writes the FastAPI schema to `DATA_DIR/openapi.json` (default `../data/openapi.json`) via `bin/generate-openapi-docs.sh`, then runs `@hey-api/openapi-ts` into `frontend/app/client/`.
