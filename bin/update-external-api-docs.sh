#!/usr/bin/env bash

# Refresh vendored OpenAPI specs from OpenRouter and Artificial Analysis.
# These files are reference-only for implementing against their APIs — not used
# at runtime and not the FastAPI export in DATA_DIR/openapi.json.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

mkdir -p api-docs

OR_URL="https://openrouter.ai/openapi.json"
AA_URL="https://artificialanalysis.ai/api/v2/openapi"

OR_OUT="api-docs/openapi-openrouter.json"
AA_OUT="api-docs/openapi-artificialanalysis.yaml"

echo "Fetching OpenRouter OpenAPI from ${OR_URL}"
curl -fsSL "${OR_URL}" -o "${OR_OUT}"

echo "Fetching Artificial Analysis OpenAPI from ${AA_URL}"
curl -fsSL "${AA_URL}" -o "${AA_OUT}"

echo "Updated external API docs:"
ls -lh "${OR_OUT}" "${AA_OUT}"
