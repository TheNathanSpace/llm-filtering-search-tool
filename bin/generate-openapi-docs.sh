#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source .venv/bin/activate

# FastAPI OpenAPI export consumed by `bin/install-frontend-api-client.sh`.
# Path matches default DATA_DIR (./data relative to repo root / .env location).
mkdir -p data
python -c "from llm_rankings import api; import json; print(json.dumps(api.app.openapi(), indent=4))" > data/openapi.json
