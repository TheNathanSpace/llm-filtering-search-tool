# LLM Filtering Search Tool

The goal is to consolidate multidimensional LLM metrics and benchmarks into a searchable platform.

## Motivation

What are the things I value in a completion large language model? Do I care about intelligence, price, or throughput?
You can try to compare these things on the [OpenRouter Rankings page](https://openrouter.ai/rankings), or
the [Artificial Analysis models page](https://artificialanalysis.ai/models), but neither of those tools really let you
expand your search beyond the few models you can see on the page.

The goal of this project is to:

1. Gather the latest model benchmarks and metrics from external metadata sources.
2. Allow a user to filter and sort models by all possible properties.
3. Generate some nice plots based on the user's specifications.

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

## Technical Overview

1. Download model data from the [Artificial Analysis API](https://artificialanalysis.ai/api-reference#models-endpoint).
2. Download model data from the [OpenRouter API](https://openrouter.ai/docs/api/api-reference/models/get-models).
3. Pair up Artificial Analysis benchmarks and OpenRouter models
4. Populate an SQLite database with the model data.
5. Expose the data via a REST API back-end.
6. Create a Next.js front-end to retrieve the data and display it in
   an [MUI Data Grid](https://mui.com/x/react-data-grid/).

More detail: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).

## Prerequisites

- Python 3.12+
- Node.js and npm (recent LTS recommended)
- Artificial Analysis and OpenRouter API keys (see [Configuration](#configuration))

## Configuration

1. Copy the env template and edit values:

   ```bash
   cp .env.template .env
   ```

2. Set the variables documented in [`.env.template`](.env.template):
   - `AA_API_KEY` — Artificial Analysis API key for benchmark data
   - `OR_API_KEY` — OpenRouter API key for model/pricing metadata
   - `DATA_DIR` — path for SQLite DB and related files (default `./data`, relative to the `.env` location)

`.env` is gitignored. The back-end loads it via `python-dotenv` when fetching or writing data.

## Development

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

Preferred (API on port 8000, Next.js on port 3030):

```bash
./bin/start-full-stack-live.sh
```

Or start each side separately:

```bash
./bin/start-backend-live.sh
./bin/start-frontend-live.sh
```

With the virtualenv activated, you can also start the API manually:

- `python backend/llm_rankings/api.py`
- `uvicorn llm_rankings.api:app --reload`

Then open the UI at [http://localhost:3030](http://localhost:3030). Interactive API docs are at
[http://localhost:8000/docs](http://localhost:8000/docs).

### Seed or refresh model data

`DATA_DIR` is gitignored, so a fresh clone has no database until you populate it. With the API running and `.env`
configured:

```bash
curl -X POST http://localhost:8000/refresh
```

Or, with the virtualenv activated and without starting the server:

```bash
python -m llm_rankings.database
```

That wipes `DATA_DIR/database.db` (if present), fetches from both APIs, matches models, and writes SQLite.

### Regenerate the front-end API client

After changing the FastAPI surface, regenerate OpenAPI and the TypeScript client:

```bash
./bin/install-frontend-api-client.sh
```

## Generative AI Disclosure

This project was developed with the assistance of an LLM coding agent. When work was off-loaded to the LLM, all aspects
of its implementation were read, verified, tested, and then modified by me to ensure they were accurate and up to my
standards.

## To Do

- [ ] Add modalities to models, so that you can filter by those that accept both text *and* image.
