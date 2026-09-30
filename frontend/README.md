# Front-end Docs

- <https://nextjs.org/docs/app/getting-started>
- <https://mui.com/toolpad/core/introduction/>
- <https://mui.com/material-ui/all-components/>
- <https://mui.com/x/react-data-grid/>

## Logging

On server start, [`instrumentation.ts`](instrumentation.ts) tees Node.js `console.*` output (and
`onRequestError` events) to `DATA_DIR/logs/latest.log` — the symlink maintained by the back-end —
using `DATA_DIR` and `LOG_LEVEL` from the repo-root `.env`. Lines are skipped until that symlink
exists (start the API first, or restart the front-end after the API). Browser/client logs are not
written to the file.

Next work (plots): [`docs/todo.md`](../docs/todo.md).

## Model filters

Filter UI and logic live under `app/filters/`:

| Module                                                                          | Role                                           |
| ------------------------------------------------------------------------------- | ---------------------------------------------- |
| `model-filters.tsx`                                                             | Filter panel layout                            |
| `filter-option.tsx`                                                             | Shared label + control row                     |
| `multi-select-filter.tsx` / `date-range-filter.tsx` / `number-range-filter.tsx` / `text-filter.tsx` | Reusable range, select, and text controls |
| `checkbox-row-filter.tsx`                                                       | Row of checkboxes with a label under each      |
| `modality-options.ts`                                                           | Input and output modality checkbox options     |
| `filter-types.ts`                                                               | Filter state and bounds types                  |
| `filter-bounds.ts`                                                              | Derive min/max and unique creators from models |
| `apply-filters.ts`                                                              | Pure `filterModels()`                          |
| `use-model-filters.ts`                                                          | State + filtered rows for the table            |

The panel lays those controls out in two columns and balances them so each column is about the same height. A control stays in one column (it is not split across the break).

`model-table.tsx` only composes the filter panel and Data Grid. Column definitions live in
`app/columns.tsx`. Column-backed filters follow that column order. The missing-values switch stays
first. Provider and modality filters have no column, so they come after the column-aligned controls.
The name cell links to the model’s OpenRouter page.
Creator values in the table and the creator filter use the catalog display name (the `OpenAI:` prefix
on the model name), not the lowercase author slug.
The modality filters keep models that include **every** checked type (unchecked means no constraint).
Numeric range controls (`NumberRangeFilter`, including size) show the selected minimum and maximum under the slider.
Click either number to type a value; Enter or leaving the field applies it, and Escape cancels.
The value is kept inside the data bounds. If it crosses the other end, that end moves with it so the range stays ordered.
Date range filters stay slider-only.

### Adding a new filter

Reuse an existing control (`MultiSelectFilter`, `DateRangeFilter`, `NumberRangeFilter`, `TextFilter`, or `CheckboxRowFilter`) when
possible. Only add a new control component if the interaction pattern is new.

1. **`filter-types.ts`** — Add the field to `ModelFiltersState` and `UserFilterChoices` (and to `FilterBounds` if it
   needs min/max or option lists derived from the data). Update `createInitialUserChoices` and `resolveFilters` with a
   sensible default (e.g. `[]` for multi-select, `""` for text, `undefined` for bounds-backed ranges).
2. **`filter-bounds.ts`** — If the filter needs bounds or options from the model list, compute them in
   `getFilterBounds`.
3. **`apply-filters.ts`** — Teach `filterModels` how to apply the new field. Respect `includeMissing` for nullable model
   properties.
4. **`model-filters.tsx`** — Render the control and wire `onChange` (and `value` when controlled) into `setFilters`.

No changes to `model-table.tsx` are needed for a new filter.

## Running

Use Docker Compose from the repo root (see the root [README](../README.md)):

```bash
# production-like (default)
docker compose up --build

# hot-reload frontend + backend
COMPOSE_PROFILES=dev docker compose up --build
```

Open `http://localhost:<FRONTEND_PORT>` (default [http://localhost:3030](http://localhost:3030)).
The browser calls same-origin `/api/*`; [`proxy.ts`](proxy.ts) rewrites those requests at runtime to
`http://<BACKEND_HOST>:<BACKEND_PORT>`. Compose `dev` sets `BACKEND_HOST=backend` (service name);
`0.0.0.0` is mapped to `127.0.0.1` for same-container bind-all. Host/port are read per request, so
Compose overrides do not require rebuilding.

Optional host `npm` install (lint / API client regen only): `../bin/setup-frontend.sh`.

### API Client

1. The back-end OpenAPI schema is exported to `DATA_DIR/openapi.json` (default `../data/openapi.json`) via
   FastAPI (`bin/generate-openapi-docs.sh`).
2. The front-end API client is generated via `@hey-api/openapi-ts` from that file.
3. The front-end API client is imported into the front-end app, and the endpoints and models/types are able to be used.

This process can be completed by running the `../bin/install-frontend-api-client.sh` script.
