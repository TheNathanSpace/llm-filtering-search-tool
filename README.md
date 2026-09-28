# LLM Filtering Search Tool

The goal is to consolidate multidimensional LLM metrics and benchmarks into a searchable platform.

## Motivation

What are the things I value in a completion large language model? Do I care about intelligence, price, or throughput?
You can try to compare these things on the [OpenRouter Rankings page](https://openrouter.ai/rankings),
but that tool does not really let you expand your search beyond the few models you can see on the page.

The goal of this project is to:

1. Gather the latest model benchmarks and metrics from external metadata sources.
2. Allow a user to filter and sort models by all possible properties.
3. Generate some nice plots based on the user's specifications.

Product requirements and status for those goals: [`docs/requirements.md`](docs/requirements.md).
Engineering backlog (aggregate provider price/speed onto model rows, then throughput filter):
[`docs/todo.md`](docs/todo.md).

And, the intent is, given these tools, it will be easier for you to decide which LLM is best for your specific
situation.

Here are the metrics I care about:

- Intelligence
- Price
- Throughput (tokens/second)
- Context Window
- Release Date

So that's five dimensions. No platform that I can find out there has a tool that lets you sort and filter all possible
models by these more complex metrics. In my ideal world, I would be able to set the following parameters:

| Metric         | My Filter                    |
|----------------|------------------------------|
| Intelligence   |                              |
| Price          | $/1M output tokens <= \$1.50 |
| Throughput     | \>= 150 tokens/s             |
| Context Window | \>= 750,000 tokens           |
| Release Date   | \>= Oct. 2025                |

And then I could sort from highest to lowest intelligence, probably choosing the highest-ranked one!

Today the table ships with Intelligence / Coding / Agentic columns (default sort: intelligence
descending) and matching range filters; context-window and creation-date filters; dedicated
pricing and throughput columns/filters exist but model-level values are empty until we aggregate
from per-provider OpenRouter endpoints (already stored in SQLite). See [`docs/todo.md`](docs/todo.md) §1.

## Technical Overview

**Current pipeline:**

1. Download model data from the [OpenRouter API](https://openrouter.ai/docs/api/api-reference/models/get-models).
2. For each catalog model, fetch per-provider endpoints (pricing + throughput/latency).
3. Enrich with open-weights flags from [models.dev](https://models.dev) and parameter counts from the
   Hugging Face Hub (when OpenRouter provides a `hugging_face_id`). Optionally gap-fill remaining
   nulls for open-weights, size, and knowledge cutoff via OpenRouter chat + Exa web search
   (`OR_WEB_ENRICHMENT=1`).
4. Drop OpenRouter models whose provider id starts with `~`, then map each remaining model into a
   `CombinedModel` (embedded AA indices become `benchmark_or_*`; list-level pricing/speed left null).
5. Populate SQLite with `models` and `model_provider_endpoints`.
6. Expose the data via a REST API back-end.
7. Create a Next.js front-end to retrieve the data and display it in
   an [MUI Data Grid](https://mui.com/x/react-data-grid/).

More detail: [backend/README.md](backend/README.md) (including [logging](backend/README.md#logging)),
[frontend/README.md](frontend/README.md) (including [logging](frontend/README.md#logging)),
[`docs/status.md`](docs/status.md) (pickup).
Upstream OpenAPI specs for implementation reference live in [`api-docs/`](api-docs/)
(refresh with `./bin/update-external-api-docs.sh`).

## Prerequisites

- Python 3.12+
- Node.js and npm (recent LTS recommended)
- OpenRouter API key (see [Configuration](#configuration))

## Configuration

1. Copy the env template and edit values:

   ```bash
   cp .env.template .env
   ```

2. Set the variables documented in [`.env.template`](.env.template):
   - `OR_API_KEY` — OpenRouter API key for models, per-provider endpoints, and embedded benchmarks
   - `OR_WEB_ENRICHMENT` — optional; set to `1` to gap-fill missing open-weights / size / knowledge cutoff via chat + Exa
   - `OR_ENRICHMENT_MODEL` — required when web enrichment is on (OpenRouter chat model id)
   - `HF_TOKEN` — optional Hugging Face Hub token (higher rate limits for size enrichment)
   - `DATA_DIR` — path for SQLite DB, logs, caches, and related files (default `./data`, relative to the `.env` location)
   - `LOG_LEVEL` — log level for the back-end and for front-end lines written to `latest.log`
     (`DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`)
   - `LOG_FILE_COUNT` — max number of timestamped `DATA_DIR/logs/*.log` files to keep (oldest deleted on
     startup; `latest.log` symlink is excluded)
   - `BACKEND_HOST` — FastAPI listen address (default `127.0.0.1`; use `0.0.0.0` to expose the API externally)
   - `BACKEND_PORT` — FastAPI listen port (default `8000`)
   - `FRONTEND_PORT` — Next.js listen port (default `3030`)

`.env` is gitignored. The back-end loads it via `python-dotenv` (discovered from the working
directory, or an explicit path via `--env-file` / `-e` or `LLM_RANKINGS_ENV_FILE`) and binds
uvicorn to `BACKEND_HOST`:`BACKEND_PORT`.
The front-end listens on `FRONTEND_PORT`. The browser calls `/api/*` on the front-end; `frontend/proxy.ts`
rewrites those requests at runtime to `http://<BACKEND_HOST>:<BACKEND_PORT>` (mapping `0.0.0.0` →
`127.0.0.1` so Next.js can reach a bind-all server on loopback). Host and port are read from the process
environment when each request is proxied, so they can change at container/app start without rebuilding.
In Docker, the image installs the back-end from `backend/pyproject.toml` (non-editable; no `[dev]` extras).
Supervisord starts both processes using the same variables: uvicorn runs `llm_rankings.api:app` bound to
`BACKEND_HOST`:`BACKEND_PORT` (image defaults `0.0.0.0` / `8000`), and Next.js listens on `FRONTEND_PORT`
(default `3030`). Override with `-e FRONTEND_PORT=...` / `-e BACKEND_HOST=...` / `-e BACKEND_PORT=...`.
The image `EXPOSE 3030` is build-time metadata for that default only — it does not change when you override
`FRONTEND_PORT`. Publish with `-p host:container` where the container port matches the runtime listen port
(e.g. `-p 3030:3030`, or `-e FRONTEND_PORT=4000 -p 4000:4000`).

Compose (`docker compose up --build`) mounts `./data` and `./.env`, forces `BACKEND_HOST=0.0.0.0` so the API
listens inside the container, publishes `${FRONTEND_PORT:-3030}`, and health-checks
`http://127.0.0.1:${BACKEND_PORT:-8000}/health`.

## Development

Parallel agent edits: use Cursor **`/worktree`** (or Agents Window New Worktree).
New worktrees run [`.cursor/worktrees.json`](.cursor/worktrees.json) for env + backend/frontend setup.
Merge into primary `main` only with explicit go-ahead, then delete the worktree and branch —
[`.cursor/rules/feature-branches.mdc`](.cursor/rules/feature-branches.mdc).


### Install

Set up the Python virtualenv and back-end package (creates `.venv` and installs `llm-rankings` editable with
dev extras, including `pre-commit`):

```bash
./bin/setup-backend.sh
source .venv/bin/activate
```

Install front-end dependencies:

```bash
./bin/setup-frontend.sh
```

Install Git hooks and verify the tree passes lint (required for local development):

```bash
./bin/run-precommit.sh
```

That runs `pre-commit install` and `pre-commit run --all-files`. Hooks must stay installed so commits are checked
automatically. Equivalent manual steps: `pip install pre-commit && pre-commit install && pre-commit run --all-files`.

### Run

Preferred (API on `BACKEND_HOST`:`BACKEND_PORT`, default `127.0.0.1:8000`; Next.js on
`FRONTEND_PORT`, default `3030`):

```bash
./bin/start-full-stack-live.sh
```

Or start each side separately:

```bash
./bin/start-backend-live.sh
./bin/start-frontend-live.sh
```

Pass a custom env file to the back-end with `--env-file` (or `-e`):

```bash
./bin/start-backend-live.sh --env-file /path/to/.env
./bin/start-full-stack-live.sh --env-file /path/to/.env
```

With the virtualenv activated, you can also start the API manually (reads host/port from `.env`):

- `python backend/llm_rankings/api.py`
- `python backend/llm_rankings/api.py --env-file /path/to/.env`
- `python -m llm_rankings.database --env-file /path/to/.env`
- `uvicorn llm_rankings.api:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"`
  (set `LLM_RANKINGS_ENV_FILE` when not using the default repo-root `.env`)

Then open the UI at `http://localhost:<FRONTEND_PORT>` (default
[http://localhost:3030](http://localhost:3030)). Interactive API docs are at
`http://localhost:<BACKEND_PORT>/docs` (default [http://localhost:8000/docs](http://localhost:8000/docs)).

### Seed or refresh model data

`DATA_DIR` is gitignored, so a fresh clone has no database until it is populated. On API startup
(and about every hour while the API is up), the back-end runs a hard-capped refresh: if
`DATA_DIR/database.db` is missing or the last successful refresh in `DATA_DIR/cache/last_refresh.json`
is ≥24 hours old, it wipe-rebuilds SQLite via the normal OpenRouter → enrich → write pipeline
(requires `.env` with `OR_API_KEY`). Within 24 hours, refresh is a no-op (no force bypass).
OpenRouter and models.dev responses are reused from `DATA_DIR/cache/` when still fresh; HF is
cached permanently per repo id (new ids still fetch on miss).

To request a refresh while the API is running (skipped if still within the 24h window):

```bash
curl -X POST "http://localhost:${BACKEND_PORT:-8000}/refresh"
```

Lifetime enrichment spend and last successful refresh time (for the UI footer) are available at
`GET /meta` (`enrichment_cost_usd`, `last_refresh_at`).

Or, with the virtualenv activated and without starting the server:

```bash
python -m llm_rankings.database
```

Both use the same gate. A successful rebuild wipes `DATA_DIR/database.db` (if present) and rewrites
it; a skip leaves the DB untouched and returns/logs that data is already fresh.

### Regenerate the front-end API client

After changing the FastAPI surface, regenerate OpenAPI and the TypeScript client:

```bash
./bin/install-frontend-api-client.sh
```

That writes FastAPI's OpenAPI schema to `DATA_DIR/openapi.json` (default `./data/openapi.json`), then
runs `@hey-api/openapi-ts` into `frontend/app/client/`.

### Refresh external API OpenAPI specs

Vendored OpenRouter OpenAPI under [`api-docs/`](api-docs/) is for implementation reference only
(not used at runtime). Refresh it with:

```bash
./bin/update-external-api-docs.sh
```

See [api-docs/README.md](api-docs/README.md).

## Generative AI Disclosure

This project was developed with the assistance of an LLM coding agent. When work was off-loaded to the LLM, all aspects
of its implementation were read, verified, tested, and then modified by me to ensure they were accurate and up to my
standards.
