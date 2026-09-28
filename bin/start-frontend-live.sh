#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Load FRONTEND_PORT (and other vars) from the repo-root .env.
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${FRONTEND_PORT:?FRONTEND_PORT is missing from .env (see .env.template)}"

cd frontend
npx next dev -p "$FRONTEND_PORT"
