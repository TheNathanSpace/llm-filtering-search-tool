#!/usr/bin/env bash

if [ ! -d "backend" ]; then
  echo "Error!"
  echo "Expected directory 'backend' does not exist. Are you running this from the correct location?"
  echo "You should be executing: ./bin/run-precommit.sh"
  exit 1
fi

pre-commit install
pre-commit run --all-files
