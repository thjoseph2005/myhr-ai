#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true
make setup

echo "Bootstrap complete. Update .env, place data/HRPolicy.pdf, then run 'make ingest' and 'make dev'."
