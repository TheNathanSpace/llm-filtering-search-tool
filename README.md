# LLM Filtering Search Tool

Consolidate multidimensional LLM metrics and benchmarks into a searchable platform.

| Doc | Contents |
| --- | --- |
| [`docs/requirements.md`](docs/requirements.md) | Requirement IDs, priority, status |
| [`docs/status.md`](docs/status.md) | What ships; column and filter map |
| [`docs/todo.md`](docs/todo.md) | Open work and decisions |
| [`backend/README.md`](backend/README.md) | Pipeline, refresh, [logging](backend/README.md#logging) |
| [`frontend/README.md`](frontend/README.md) | Filters, page URL, [logging](frontend/README.md#logging) |
| [`api-docs/README.md`](api-docs/README.md) | Vendored upstream OpenAPI |

## Example

| Metric | Example |
| --- | --- |
| Intelligence | — |
| Price | $/1M output tokens <= \$1.50 |
| Throughput | \>= 150 tokens/s |
| Context Window | \>= 750,000 tokens |
| Release Date | \>= Oct. 2025 |

Then sort by intelligence, highest first.

## Prerequisites

- Docker Engine with Compose v2
- OpenRouter API key
- Optional, for local builds, lint hooks, OpenAPI client regen, and agent worktrees: Python 3.12+ and Node.js/npm

## Run

Copy [`docker-compose.yaml`](docker-compose.yaml). Set `OR_API_KEY` in that file’s `environment:` block.

```bash
docker compose up -d
```

UI: [http://localhost:3030](http://localhost:3030).

| Item | Detail |
| --- | --- |
| Image | `ghcr.io/thenathanspace/llm-filtering-search-tool:latest`. The package must be public, or run `docker login ghcr.io` first. Pin a release tag instead of `latest` for a fixed build. |
| Data | SQLite, logs, and caches in `./data` next to the compose file |
| API | Front-end `/api` proxy only |
| Port | Change the host side of `ports:`. The container side must match `FRONTEND_PORT`. |

[`.env.template`](.env.template) is optional. Copy it to `.env` and use `env_file` instead of inlining `environment:`.

## Configuration

Server deploys set variables in `docker-compose.yaml`. Local builds and host tooling:

```bash
cp .env.template .env
```

| Variable | Required | Value |
| --- | --- | --- |
| `OR_API_KEY` | yes | OpenRouter API key for models, per-provider endpoints, and embedded benchmarks |
| `OR_WEB_ENRICHMENT` | no | `1` gap-fills missing open-weights and, for open models, size. See [SRC-12](docs/requirements.md#src-12). |
| `HF_TOKEN` | no | Hugging Face Hub token (higher rate limits for size enrichment) |
| `DATA_DIR` | | SQLite, logs, and caches. Relative paths resolve from the `.env` directory when that file is loaded, otherwise from the working directory. Server compose sets `/app/data`. |
| `HOST_DATA_DIR` | local Compose | Host path bind-mounted to `/app/data` (default `./data`). Worktree setup points this at the primary checkout’s `data/`. |
| `LOG_LEVEL` | | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` for the back-end and for front-end lines in `latest.log` |
| `LOG_FILE_COUNT` | | Max timestamped `DATA_DIR/logs/*.log` files. Oldest deleted on startup. `latest.log` is excluded. |
| `BACKEND_HOST` | | FastAPI listen address (default `127.0.0.1` on the host). Containers use `0.0.0.0`. |
| `BACKEND_PORT` | | FastAPI listen port (default `8000`) |
| `ENABLE_API_DOCS` | no | `1` enables FastAPI `/docs`, `/redoc`, and `/openapi.json`. Off by default. The local `dev` profile turns it on. |
| `EXPORT_BASE_URL` | no | Public origin (`http://host:3030`, no path). See [Refresh](backend/README.md#refresh). |
| `TZ` | no | IANA timezone for container log timestamps (default `Etc/UTC`). Example: `America/Denver`. |
| `FRONTEND_PORT` | | Next.js listen port (default `3030`) |
| `COMPOSE_PROFILES` | local Compose | `prod` (default) or `dev` (hot reload) |

`.env` is gitignored. Local compose loads it with `env_file` and mounts it at `/app/.env`. The back-end reads the process environment first and fills gaps from a `.env` file (`python-dotenv`, or `--env-file` / `-e` / `LLM_RANKINGS_ENV_FILE`). Values already set in the environment are kept.

## Local build

[`docker-compose.local.yaml`](docker-compose.local.yaml) builds from this checkout.

> [!WARNING]
> Set exactly one of `prod` or `dev`. `COMPOSE_PROFILES=prod` together with `--profile dev` starts both stacks.

| Profile | Command | Runs |
| --- | --- | --- |
| `prod` (default) | `docker compose -f docker-compose.local.yaml up --build` | One image: FastAPI + Next.js standalone under supervisord. Mounts `./data` (or `HOST_DATA_DIR`) and `./.env`. Forces `BACKEND_HOST=0.0.0.0`. Publishes `${FRONTEND_PORT:-3030}`. Health check `http://127.0.0.1:${BACKEND_PORT:-8000}/health`. API is not published. |
| `dev` | `COMPOSE_PROFILES=dev docker compose -f docker-compose.local.yaml up --build` | Separate `backend` and `frontend` services, bind mounts, `uvicorn --reload` and `next dev`. The front-end proxies to the service name `backend`. Swagger (`ENABLE_API_DOCS` forced on): [http://localhost:8000/docs](http://localhost:8000/docs). |

Set `COMPOSE_PROFILES=dev` in `.env` to use the `prod` command for the `dev` profile.

## Releases

A push to `main` runs [`.github/workflows/release.yml`](.github/workflows/release.yml).

| Item | Value |
| --- | --- |
| Release | GitHub Release. Body is the commit subjects and short hashes since the previous tag. |
| Tag | `v<YYYY.MM.DD>-<7-char sha>` from the commit date (UTC) |
| Image | Dockerfile final stage, pushed as that tag and as `latest` to `ghcr.io/thenathanspace/llm-filtering-search-tool` |
| First push | The package is private. Mark it public once; later tags keep that visibility. Public is permanent. |
| Permissions | `contents: write` and `packages: write`, when the repository’s Actions workflow permissions allow read and write (the GitHub default) |

```bash
docker pull ghcr.io/thenathanspace/llm-filtering-search-tool:latest
```

[`docker-compose.yaml`](docker-compose.yaml) pulls that image. [`docker-compose.local.yaml`](docker-compose.local.yaml) does not.

## Development

### Worktrees

- Cursor `/worktree`, or Agents Window **New Worktree**.
- Setup: [`.cursor/worktrees.json`](.cursor/worktrees.json) (env, optional host tooling, `HOST_DATA_DIR` → the primary checkout’s `data/`).
- Merge into primary `main` only with explicit go-ahead (`merge --ff-only`). Landing deletes that task’s worktree and branch. [`.cursor/rules/feature-branches.mdc`](.cursor/rules/feature-branches.mdc).

### Worktree UI preview

One Compose stack at a time (shared container names and ports).

```bash
# HOST_DATA_DIR points at the primary checkout's data/ (worktree setup sets this).
COMPOSE_PROFILES=dev docker compose -f docker-compose.local.yaml up --build -d
```

Stop with `docker compose -f docker-compose.local.yaml down` before landing or when done verifying. Agents start and stop preview only when asked. Land cleanup stops the preview stack first.

### Host tooling

For pre-commit hooks, the TypeScript API client, and agent worktrees. Not required to run the app.

```bash
./bin/setup-backend.sh
source .venv/bin/activate
./bin/setup-frontend.sh
./bin/run-precommit.sh
```

`./bin/run-precommit.sh` runs `pre-commit install` and `pre-commit run --all-files`. Hooks must stay installed.

### Refresh model data

`DATA_DIR` is gitignored. A fresh clone has no database until refresh. Mechanism: [backend/README.md](backend/README.md#refresh).

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

### Regenerate the front-end API client

After changing the FastAPI surface (requires host tooling above):

```bash
./bin/install-frontend-api-client.sh
```

Writes `DATA_DIR/openapi.json` (default `./data/openapi.json`), then `@hey-api/openapi-ts` into `frontend/app/client/`.

### Refresh external API OpenAPI specs

Vendored OpenRouter OpenAPI under [`api-docs/`](api-docs/) is implementation reference only (not used at runtime).

```bash
./bin/update-external-api-docs.sh
```

See [api-docs/README.md](api-docs/README.md).

## Generative AI Disclosure

80% of this app was vibe coded.
