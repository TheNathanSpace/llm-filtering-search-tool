#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd $SCRIPT_DIR/..
./bin/generate-openapi-docs.sh

cd frontend
npx @hey-api/openapi-ts -i ../data/openapi.json -o app/client
