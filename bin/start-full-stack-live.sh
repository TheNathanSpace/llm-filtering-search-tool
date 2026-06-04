#!/usr/bin/env bash

# This script starts both the back‑end (FastAPI via uvicorn) and the front‑end (Next.js) in
# subprocesses so that a single command can launch the full development stack.
# When the script receives a termination signal (e.g., Ctrl+C), it forwards the signal
# to the child processes and waits for them to exit, ensuring a clean shutdown.

set -e

# Resolve the directory of this script. The start scripts in bin already handle
# changing to the project root, so we can invoke them directly via their absolute
# paths without performing an additional `cd` here.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Start the backend server in the background using the dedicated script.
"$SCRIPT_DIR/start-backend-live.sh" &
BACKEND_PID=$!

# Start the frontend dev server in the background using its dedicated script.
"$SCRIPT_DIR/start-frontend-live.sh" &
FRONTEND_PID=$!

# ---------------------------------------------------------------------------
# Cleanup function to stop both processes.
# ---------------------------------------------------------------------------
cleanup() {
    echo "Shutting down development servers..."
    # Kill the child processes if they are still running.
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    # Wait for them to exit to avoid zombie processes.
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap termination signals (Ctrl+C -> SIGINT, and SIGTERM) and invoke cleanup.
trap cleanup SIGINT SIGTERM

# Wait for both background jobs to finish. `wait` will return when the first
# job exits; the cleanup trap will then terminate the remaining job.
wait $BACKEND_PID $FRONTEND_PID
