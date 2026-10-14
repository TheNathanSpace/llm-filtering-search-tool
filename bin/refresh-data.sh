#!/usr/bin/env bash

# Ops helper: force or gated model-data refresh inside the running Compose container.
# Forwards args to: python -m llm_rankings.refresh
#
# Examples:
#   ./bin/refresh-data.sh
#   ./bin/refresh-data.sh --force
#   ./bin/refresh-data.sh --force --source hf
#   ./bin/refresh-data.sh --force --source models --source models-dev

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  if [[ -x .venv/bin/python ]]; then
    exec .venv/bin/python -m llm_rankings.refresh --help
  fi
  exec python -m llm_rankings.refresh --help
fi

resolve_container() {
  if docker container inspect llm-filtering >/dev/null 2>&1; then
    local status
    status="$(docker inspect -f '{{.State.Running}}' llm-filtering 2>/dev/null || echo false)"
    if [[ "$status" == "true" ]]; then
      echo "llm-filtering"
      return 0
    fi
  fi
  if docker container inspect llm-filtering-backend-dev >/dev/null 2>&1; then
    local status
    status="$(docker inspect -f '{{.State.Running}}' llm-filtering-backend-dev 2>/dev/null || echo false)"
    if [[ "$status" == "true" ]]; then
      echo "llm-filtering-backend-dev"
      return 0
    fi
  fi
  return 1
}

if ! container="$(resolve_container)"; then
  echo "No running app container found (tried llm-filtering, llm-filtering-backend-dev)." >&2
  echo "Start the local Compose stack (docker-compose.local.yaml) or the server stack, then retry." >&2
  exit 1
fi

# Local stacks mount /app/.env. The server compose file does not; that container
# already has its configuration in the process environment.
env_args=()
if docker exec -w /app "${container}" test -f /app/.env; then
  env_args=(--env-file /app/.env)
fi
echo "Refreshing via docker exec ${container} python -m llm_rankings.refresh ${env_args[*]} $*"
exec docker exec -w /app "${container}" python -m llm_rankings.refresh "${env_args[@]}" "$@"
