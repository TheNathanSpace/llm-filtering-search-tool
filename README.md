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
Engineering backlog (plots):
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
descending) and matching range filters; context-window and creation-date filters; and price
range filters. Input/output price, the chosen provider, median throughput, and median latency
come from one OpenRouter host: the cheapest listed 90/10 input/output blend, unless the next
host is much faster on both. The panel can filter that provider, throughput, and latency.
See [`docs/todo.md`](docs/todo.md).

## Technical Overview

**Current pipeline:**

1. Download model data from the [OpenRouter API](https://openrouter.ai/docs/api/api-reference/models/get-models).
2. For each catalog model, fetch per-provider endpoints (pricing + throughput/latency).
3. Enrich with open-weights flags from [models.dev](https://models.dev) and parameter counts from the
   Hugging Face Hub (when OpenRouter provides a `hugging_face_id`). Optionally gap-fill remaining
   nulls for open-weights, size, and knowledge cutoff via OpenRouter chat + Exa web search
   (`OR_WEB_ENRICHMENT=1`).
4. Drop non-comparable OpenRouter listings (`~` providers, `:free` / `:batch`, `openrouter/*` meta, `*-router`, floating `*-latest` aliases), then map
   each remaining model into a `CombinedModel` (embedded AA indices become `benchmark_or_*`).
   Listed price and median throughput/latency are copied from the chosen provider endpoint.
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

- Docker Engine with Compose v2
- OpenRouter API key (see [Configuration](#configuration))

Optional (lint hooks, OpenAPI client regen, agent worktrees): Python 3.12+ and Node.js/npm.

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
   - `HOST_DATA_DIR` — optional host path Compose bind-mounts to `/app/data` (default `./data`); worktree setup points this at the primary checkout’s `data/`
   - `LOG_LEVEL` — log level for the back-end and for front-end lines written to `latest.log`
     (`DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`)
   - `LOG_FILE_COUNT` — max number of timestamped `DATA_DIR/logs/*.log` files to keep (oldest deleted on
     startup; `latest.log` symlink is excluded)
- `BACKEND_HOST` — FastAPI listen address for host tooling (default `127.0.0.1`); Compose overrides this inside containers
- `BACKEND_PORT` — FastAPI listen port (default `8000`)
- `ENABLE_API_DOCS` — optional; set to `1` for FastAPI `/docs` / `/redoc` / `/openapi.json` (off by default; Compose `dev` enables it)
- `FRONTEND_PORT` — Next.js listen port (default `3030`)
- `COMPOSE_PROFILES` — Compose stack to start: `prod` (default) or `dev` (hot reload)

`.env` is gitignored. Compose loads it via `env_file` and mounts it at `/app/.env`. The back-end also
reads it via `python-dotenv` (or `--env-file` / `-e` / `LLM_RANKINGS_ENV_FILE`). The browser calls
`/api/*` on the front-end; `frontend/proxy.ts` rewrites those requests at runtime to
`http://<BACKEND_HOST>:<BACKEND_PORT>` (mapping `0.0.0.0` → `127.0.0.1` for same-container bind-all).
Host and port are read when each request is proxied, so Compose `environment:` overrides apply without
rebuilding.

## Run (Docker Compose)

Profiles are mutually exclusive — set exactly one of `prod` or `dev` via `COMPOSE_PROFILES` in `.env`
(or prefix the command). Do not combine `COMPOSE_PROFILES=prod` with `--profile dev` (both stacks would
start and fight over ports).

### Production-like (default)

Single image: FastAPI + Next.js standalone under supervisord. Mounts `./data` and `./.env`, forces
`BACKEND_HOST=0.0.0.0`, publishes `${FRONTEND_PORT:-3030}`, and health-checks
`http://127.0.0.1:${BACKEND_PORT:-8000}/health`.

```bash
docker compose up --build
```

Open the UI at `http://localhost:<FRONTEND_PORT>` (default
[http://localhost:3030](http://localhost:3030)). With the default profile the API is only reached
through the front-end `/api` proxy (not published on the host).

### Development profile

Separate `backend` and `frontend` services with bind mounts and hot reload (`uvicorn --reload`,
`next dev`). The front-end proxies to the Compose service name `backend`.

```bash
COMPOSE_PROFILES=dev docker compose up --build
```

Or set `COMPOSE_PROFILES=dev` in `.env` and run `docker compose up --build`.

UI: [http://localhost:3030](http://localhost:3030). API docs (Swagger; `ENABLE_API_DOCS`
forced on by the Compose `dev` profile):
[http://localhost:8000/docs](http://localhost:8000/docs).

## Development

Parallel agent edits: use Cursor **`/worktree`** (or Agents Window New Worktree).
New worktrees run [`.cursor/worktrees.json`](.cursor/worktrees.json) for env + optional host tooling setup
(including `HOST_DATA_DIR` → the primary checkout’s `data/` so Compose reuses the warm DB/cache).
Merge into primary `main` only with explicit go-ahead (`merge --ff-only`); landing is not finished
until that task’s worktree and branch are deleted —
[`.cursor/rules/feature-branches.mdc`](.cursor/rules/feature-branches.mdc).

### Worktree UI preview

Only one Compose stack at a time (shared container names/ports). From the task worktree, when you want
to try the branch UI:

```bash
# Ensure HOST_DATA_DIR points at the primary checkout's data/ (worktree setup sets this).
COMPOSE_PROFILES=dev docker compose up --build -d
```

UI: [http://localhost:3030](http://localhost:3030) (or `FRONTEND_PORT`). Stop with `docker compose down`
before landing or when done verifying. Agents start/stop preview only when asked; land cleanup always
stops the preview stack first.

### Host tooling (optional)

Needed for pre-commit hooks, regenerating the TypeScript API client, and agent worktrees — not for
running the app:

```bash
./bin/setup-backend.sh
source .venv/bin/activate
./bin/setup-frontend.sh
./bin/run-precommit.sh
```

`./bin/run-precommit.sh` runs `pre-commit install` and `pre-commit run --all-files`. Hooks must stay
installed so commits are checked automatically.

### Seed or refresh model data

`DATA_DIR` is gitignored, so a fresh clone has no database until it is populated. On API startup
(and about every hour while the API is up), the back-end runs a hard-capped refresh: if
`DATA_DIR/database.db` is missing or the last successful refresh in `DATA_DIR/cache/last_refresh.json`
is ≥24 hours old, it wipe-rebuilds SQLite via the normal OpenRouter → enrich → write pipeline
(requires `.env` with `OR_API_KEY`). Within 24 hours, that automatic path is a no-op.
OpenRouter models/endpoints and models.dev responses are reused from `DATA_DIR/cache/` when still
fresh; HF is cached permanently per repo id (new ids still fetch on miss).

There is no public HTTP refresh endpoint (avoids unauthenticated wipe/rebuilds on an exposed
instance). Ops can refresh from the host (same 24h gate by default, or `--force` to bypass):

```bash
# Prefer Docker when Compose is up (prod `llm-filtering` or dev `llm-filtering-backend-dev`).
# The script passes `--env-file /app/.env` (prod images cannot discover `.env` via site-packages).
./bin/refresh-data.sh
./bin/refresh-data.sh --force
./bin/refresh-data.sh --force --source hf
./bin/refresh-data.sh --force --source models --source models-dev

# Or on the host venv:
source .venv/bin/activate
python -m llm_rankings.refresh
python -m llm_rankings.refresh --force --source providers
```

`--force` invalidates selected disk caches then wipe-rebuilds SQLite. Sources: `models`,
`providers`, `models-dev`, `hf`, `enrichment`, `all` (default when `--force` has no `--source`).
Selecting `models` also busts `providers` (endpoints cache is one blob). `last_refresh_at` is the
last successful **DB rebuild** (not per-source freshness) and resets the auto 24h gate.
`python -m llm_rankings.database` is an alias for the same CLI.

A successful rebuild wipes `DATA_DIR/database.db` (if present) and rewrites it; a gated skip leaves
the DB untouched and logs that data is already fresh.

Lifetime enrichment spend and last successful refresh time (for the UI footer) are available at
`GET /meta` (`enrichment_cost_usd`, `last_refresh_at`).

### Regenerate the front-end API client

After changing the FastAPI surface, regenerate OpenAPI and the TypeScript client (requires host
tooling setup above):

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
