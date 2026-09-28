#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source .venv/bin/activate

ENV_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file|-e)
      if [[ $# -lt 2 ]]; then
        echo "error: $1 requires a path" >&2
        exit 1
      fi
      ENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Load BACKEND_HOST / BACKEND_PORT (and other vars) from the repo-root .env,
# or from --env-file when passed.
set -a
# shellcheck disable=SC1091
source "${ENV_FILE:-.env}"
set +a

if [[ -n "$ENV_FILE" ]]; then
  export LLM_RANKINGS_ENV_FILE="$ENV_FILE"
fi

: "${BACKEND_HOST:?BACKEND_HOST is missing from .env (see .env.template)}"
: "${BACKEND_PORT:?BACKEND_PORT is missing from .env (see .env.template)}"

export WATCHFILES_FORCE_POLLING=true
uvicorn llm_rankings.api:app --reload --reload-include 'backend/**' \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT"
