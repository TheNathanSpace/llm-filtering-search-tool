# Front-end Docs

- <https://nextjs.org/docs/app/getting-started>
- <https://mui.com/toolpad/core/introduction/>
- <https://mui.com/material-ui/all-components/>
- <https://mui.com/x/react-data-grid/>

Always-visible filter fields (e.g. Min Price / Max Price) would improve usability over multi-click column filters alone.

## Model filters

Filter UI and logic live under `app/filters/`:

| Module                                                                          | Role                                           |
| ------------------------------------------------------------------------------- | ---------------------------------------------- |
| `model-filters.tsx`                                                             | Filter panel layout                            |
| `filter-option.tsx`                                                             | Shared label + control row                     |
| `multi-select-filter.tsx` / `date-range-filter.tsx` / `number-range-filter.tsx` | Reusable controls                              |
| `filter-types.ts`                                                               | Filter state and bounds types                  |
| `filter-bounds.ts`                                                              | Derive min/max and unique creators from models |
| `apply-filters.ts`                                                              | Pure `filterModels()`                          |
| `use-model-filters.ts`                                                          | State + filtered rows for the table            |

`model-table.tsx` only composes the filter panel and Data Grid.

### Adding a new filter

Reuse an existing control (`MultiSelectFilter`, `DateRangeFilter`, or `NumberRangeFilter`) when possible. Only add a new
control component if the interaction pattern is new.

1. **`filter-types.ts`** — Add the field to `ModelFiltersState` and `UserFilterChoices` (and to `FilterBounds` if it
   needs min/max or option lists derived from the data). Update `createInitialUserChoices` and `resolveFilters` with a
   sensible default (e.g. `[]` for multi-select, `undefined` for bounds-backed ranges).
2. **`filter-bounds.ts`** — If the filter needs bounds or options from the model list, compute them in
   `getFilterBounds`.
3. **`apply-filters.ts`** — Teach `filterModels` how to apply the new field. Respect `includeMissing` for nullable model
   properties.
4. **`model-filters.tsx`** — Render the control and wire `onChange` (and `value` when controlled) into `setFilters`.

No changes to `model-table.tsx` are needed for a new filter.

## Installation

From the repo root:

```bash
./bin/setup-frontend.sh
./bin/start-frontend-live.sh
```

`npm run dev` (from `frontend/`) also works; the app listens on port **3030**.

Open [http://localhost:3030](http://localhost:3030). The UI talks to the back-end URL from
`NEXT_PUBLIC_BACKEND_URL` in the repo-root [`.env`](../.env.template) (default `http://localhost:8000`). For a full
local stack, see the root [README](../README.md).

### API Client

1. The back-end OpenAPI docs are generated via FastAPI's built-in tools.
2. The front-end API client is generated via @hey-api/openapi-ts.
3. The front-end API client is imported into the front-end app, and the endpoints and models/types are able to be used.

This process can be completed by running the `../bin/install-frontend-api-client.sh` script.
