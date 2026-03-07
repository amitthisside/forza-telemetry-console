.PHONY: bootstrap up down lint test format

bootstrap:
	pnpm install
	python3 -m pip install --upgrade pip
	python3 -m pip install -e packages/telemetry-models -e packages/event-contracts -e packages/forza-parser
	python3 -m pip install -e services/telemetry-ingest -e services/telemetry-stream -e services/session-service -e services/analytics-service -e services/device-gateway

up:
	docker compose up --build

down:
	docker compose down -v

lint:
	ruff check .
	pnpm -r lint

test:
	pytest
	pnpm -r test

format:
	ruff format .
	pnpm -r format
