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
range filters. The model name links to its OpenRouter page. Creator labels use the catalog’s
capitalization (`OpenAI`), not the lowercase author slug. Input/output price, median throughput,
and median latency come from one OpenRouter host: the cheapest listed 90/10 input/output blend,
unless the next host is much faster on both. The panel can filter throughput and
latency, and column-backed filters follow the table column order. Entering a token count in
millions adds a cost column left of input cost, using that same 90/10 blend, and a cost
range under the token field filters the table to that calculated cost.
See [`docs/todo.md`](docs/todo.md).

## Technical Overview

**Current pipeline:**

1. Download model data from the [OpenRouter API](https://openrouter.ai/docs/api/api-reference/models/get-models).
2. For each catalog model, fetch per-provider endpoints (pricing + throughput/latency).
3. Enrich with open-weights flags from [models.dev](https://models.dev) and parameter counts from the
   Hugging Face Hub (when OpenRouter provides a `hugging_face_id`). Optionally gap-fill remaining
   nulls for open-weights, size, and knowledge cutoff via OpenRouter Batch (GPT-6 Luna +
   OpenAI native web search; `OR_WEB_ENRICHMENT=1`; refresh waits on the batch in the
   background while the live DB keeps serving).
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
- OpenRouter API key

Optional (local builds, lint hooks, OpenAPI client regen, agent worktrees): Python 3.12+ and Node.js/npm.

## Run on a server

Copy [`docker-compose.yaml`](docker-compose.yaml) onto the server. Set `OR_API_KEY` and any other
values in that file’s `environment:` block, then:

```bash
docker compose up -d
```

That pulls `ghcr.io/thenathanspace/llm-filtering-search-tool:latest` (the package must be public, or
run `docker login ghcr.io` first). The UI is at [http://localhost:3030](http://localhost:3030).
SQLite, logs, and caches persist in `./data` next to the compose file. The API is only reached
through the front-end `/api` proxy.

Change the host side of `ports:` to publish a different port. The container side must match
`FRONTEND_PORT`. Pin the image tag to a release tag instead of `latest` for a fixed build.

[`.env.template`](.env.template) is optional. People who prefer a separate env file can copy it to
`.env` and use `env_file` instead of inlining `environment:`.

## Configuration

Server deploys set variables in `docker-compose.yaml`. Local builds and host tooling use a `.env`
file:

```bash
cp .env.template .env
```

Variables in [`.env.template`](.env.template):

- `OR_API_KEY` — OpenRouter API key for models, per-provider endpoints, and embedded benchmarks
- `OR_WEB_ENRICHMENT` — optional; set to `1` to gap-fill missing open-weights / size / knowledge cutoff via OpenRouter Batch (hardcoded GPT-6 Luna + native web search; refresh job waits for the batch while the live DB keeps serving)
- `HF_TOKEN` — optional Hugging Face Hub token (higher rate limits for size enrichment)
- `DATA_DIR` — path for SQLite DB, logs, caches, and related files. Relative paths are resolved from the `.env` directory when that file is loaded, otherwise from the working directory. The server compose file sets `/app/data`.
- `HOST_DATA_DIR` — local Compose only; host path `docker-compose.local.yaml` bind-mounts to `/app/data` (default `./data`). Worktree setup points this at the primary checkout’s `data/`
- `LOG_LEVEL` — log level for the back-end and for front-end lines written to `latest.log`
  (`DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`)
- `LOG_FILE_COUNT` — max number of timestamped `DATA_DIR/logs/*.log` files to keep (oldest deleted on
  startup; `latest.log` symlink is excluded)
- `BACKEND_HOST` — FastAPI listen address (default `127.0.0.1` on the host). Containers use `0.0.0.0`
- `BACKEND_PORT` — FastAPI listen port (default `8000`)
- `ENABLE_API_DOCS` — optional; set to `1` for FastAPI `/docs` / `/redoc` / `/openapi.json` (off by default; local `dev` profile enables it)
- `FRONTEND_PORT` — Next.js listen port (default `3030`)
- `COMPOSE_PROFILES` — local Compose only: `prod` (default) or `dev` (hot reload)

`.env` is gitignored. The local compose file loads it with `env_file` and mounts it at `/app/.env`.
The back-end reads the process environment first and fills gaps from a `.env` file when one is
present (`python-dotenv`, or `--env-file` / `-e` / `LLM_RANKINGS_ENV_FILE`). Values already set in
the environment are kept. The browser calls `/api/*` on the front-end; `frontend/proxy.ts` rewrites
those requests at runtime to `http://<BACKEND_HOST>:<BACKEND_PORT>` (mapping `0.0.0.0` → `127.0.0.1`
for same-container bind-all). Host and port are read when each request is proxied, so Compose
`environment:` overrides apply without rebuilding.

## Local build

[`docker-compose.local.yaml`](docker-compose.local.yaml) builds from this checkout. Profiles are
mutually exclusive — set exactly one of `prod` or `dev` via `COMPOSE_PROFILES` in `.env` (or prefix
the command). Do not combine `COMPOSE_PROFILES=prod` with `--profile dev` (both stacks would start
and fight over ports).

### Production-like

Single image: FastAPI + Next.js standalone under supervisord. Mounts `./data` (or `HOST_DATA_DIR`)
and `./.env`, forces `BACKEND_HOST=0.0.0.0`, publishes `${FRONTEND_PORT:-3030}`, and health-checks
`http://127.0.0.1:${BACKEND_PORT:-8000}/health`.

```bash
docker compose -f docker-compose.local.yaml up --build
```

Open the UI at `http://localhost:<FRONTEND_PORT>` (default
[http://localhost:3030](http://localhost:3030)). The API is only reached through the front-end
`/api` proxy (not published on the host).

### Development profile

Separate `backend` and `frontend` services with bind mounts and hot reload (`uvicorn --reload`,
`next dev`). The front-end proxies to the Compose service name `backend`.

```bash
COMPOSE_PROFILES=dev docker compose -f docker-compose.local.yaml up --build
```

Or set `COMPOSE_PROFILES=dev` in `.env` and run `docker compose -f docker-compose.local.yaml up --build`.

UI: [http://localhost:3030](http://localhost:3030). API docs (Swagger; `ENABLE_API_DOCS`
forced on by the `dev` profile):
[http://localhost:8000/docs](http://localhost:8000/docs).

## Releases

A push to `main` runs [`.github/workflows/release.yml`](.github/workflows/release.yml). It creates a
GitHub Release and publishes the production image (the Dockerfile’s final stage) to GHCR.

The tag is `v<YYYY.MM.DD>-<short sha>` from the commit date (UTC). The release body is the commit
subjects since the previous tag. The image is pushed as that tag and as `latest`:

`ghcr.io/thenathanspace/llm-filtering-search-tool`

```bash
docker pull ghcr.io/thenathanspace/llm-filtering-search-tool:latest
```

The first push creates the package as private. Mark that package public once in its settings; later
tags of the same image keep that visibility. Making it public is permanent.

[`docker-compose.yaml`](docker-compose.yaml) pulls that image. Local builds use
[`docker-compose.local.yaml`](docker-compose.local.yaml) and do not pull it.
The workflow’s `contents: write` and `packages: write` permissions apply when the repository’s
Actions workflow permissions allow read and write (the GitHub default).

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
COMPOSE_PROFILES=dev docker compose -f docker-compose.local.yaml up --build -d
```

UI: [http://localhost:3030](http://localhost:3030) (or `FRONTEND_PORT`). Stop with
`docker compose -f docker-compose.local.yaml down` before landing or when done verifying. Agents
start/stop preview only when asked; land cleanup always stops the preview stack first.

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
(and about every hour while the API is up), the back-end starts a hard-capped refresh in the
**background** (API serve is not blocked): if `DATA_DIR/database.db` is missing or the last
successful refresh in `DATA_DIR/cache/last_refresh.json` is ≥24 hours old, it rebuilds via the
normal OpenRouter → enrich → staging-SQLite → atomic swap pipeline (requires `OR_API_KEY`
in the container environment or `.env`). Within 24 hours, that automatic path is a no-op. While a refresh is in flight,
callers keep reading the previous live DB (up to ~24h old is expected). OpenRouter
models/endpoints and models.dev responses are reused from `DATA_DIR/cache/` when still fresh; HF
is cached permanently per repo id (new ids still fetch on miss).

There is no public HTTP refresh endpoint (avoids unauthenticated rebuilds on an exposed
instance). Ops can refresh from the host (same 24h gate by default, or `--force` to bypass):

```bash
# Prefer Docker when Compose is up (server/local prod `llm-filtering`, or dev `llm-filtering-backend-dev`).
# Passes `--env-file /app/.env` when that mount exists; otherwise uses the container environment.
./bin/refresh-data.sh
./bin/refresh-data.sh --force
./bin/refresh-data.sh --force --source hf
./bin/refresh-data.sh --force --source models --source models-dev

# Or on the host venv:
source .venv/bin/activate
python -m llm_rankings.refresh
python -m llm_rankings.refresh --force --source providers
```

`--force` invalidates selected disk caches then rebuilds SQLite the same staging-swap way.
Sources: `models`, `providers`, `models-dev`, `hf`, `enrichment`, `all` (default when `--force`
has no `--source`). Selecting `models` also busts `providers` (endpoints cache is one blob).
`last_refresh_at` is the last successful **DB rebuild** (not per-source freshness) and resets the
auto 24h gate. `python -m llm_rankings.database` is an alias for the same CLI.

A successful rebuild writes `DATA_DIR/database.db.staging` then atomically replaces
`DATA_DIR/database.db`; a gated skip leaves the live DB untouched and logs that data is already
fresh.

Lifetime enrichment spend and last successful refresh time (for the UI footer) are available at
`GET /meta` (`enrichment_cost_usd`, `last_refresh_at`, `database_ready`,
`refresh_in_progress`). When the live DB is missing or still being built, the table empty
state explains that population is in progress and the page polls until models appear.

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
