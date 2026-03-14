SHELL := /bin/bash

.PHONY: setup dev dev-web dev-api lint test format ingest docker-up docker-down

setup:
	cd apps/web && npm install
	cd services/api && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -e .[dev]

dev:
	( cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ) & \
	( cd apps/web && npm run dev )

dev-web:
	cd apps/web && npm run dev

dev-api:
	cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	cd apps/web && npm run lint
	cd services/api && source .venv/bin/activate && ruff check app tests && mypy app

test:
	cd services/api && source .venv/bin/activate && pytest

format:
	cd apps/web && npm run format
	cd services/api && source .venv/bin/activate && ruff check --fix app tests && ruff format app tests

ingest:
	cd services/api && source .venv/bin/activate && python -m app.services.ingestion_cli --path ../../data/knowledge_base

docker-up:
	docker compose up --build

docker-down:
	docker compose down --remove-orphans
