#!/usr/bin/env bash

if [ ! -d "backend" ]; then
  echo "Error!"
  echo "Directory 'backend' does not exist. Are you running this from the correct location?"
  echo "You should be executing: ./bin/setup-backend.sh"
  exit 1
fi

python -m venv .venv
source .venv/bin/activate
cd backend
pip install -e .[dev]
