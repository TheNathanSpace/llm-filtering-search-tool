#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd $SCRIPT_DIR/..

python -m venv .venv
source .venv/bin/activate
cd backend
pip install -e .[dev]
