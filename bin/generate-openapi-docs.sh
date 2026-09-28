#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source .venv/bin/activate

# FastAPI OpenAPI export consumed by `bin/install-frontend-api-client.sh`.
# Path matches default DATA_DIR (./data relative to repo root / .env location).
# Write from Python so setup_logging() stdout does not pollute the JSON file.
# Works even when ENABLE_API_DOCS is off (interactive /docs routes disabled).
mkdir -p data
python <<'PY'
from pathlib import Path

from llm_rankings import api
import json

Path("data/openapi.json").write_text(
    json.dumps(api.app.openapi(), indent=4) + "\n",
    encoding="utf-8",
)
PY
