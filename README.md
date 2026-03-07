# Forza Telemetry Console

Production-oriented telemetry platform for Forza telemetry data out.

## Repository Layout

- `apps/web`: Main React + TypeScript operator console.
- `apps/web` routes include `/overlay` for OBS-friendly overlays.
- `services/telemetry-ingest`: UDP ingest + Forza packet decode entry service.
- `services/telemetry-stream`: WebSocket fanout service for live telemetry.
- `services/session-service`: Session lifecycle and persistence APIs.
- `services/analytics-service`: Coaching, diagnostics, and history APIs.
- `services/device-gateway`: Optional hardware adapter runtime.
- `packages/forza-parser`: Forza parser package and packet tests.
- `packages/telemetry-models`: Shared typed telemetry models.
- `packages/event-contracts`: NATS subjects and event payload contracts.
- `packages/client-sdk`: TypeScript SDK for frontend/internal clients.
- `infra`: Docker, Kubernetes, Helm, and ops scripts.
- `docs`: Product, architecture, runbooks, API, and ADRs.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- pnpm 10+
- Docker

### Bootstrap

```bash
make bootstrap
```

### Run local stack

```bash
make up
```

### Open the UI

- Main console: `http://localhost:3000/`
- Overlay route: `http://localhost:3000/overlay`

## Development Standards

- APIs versioned under `/api/v1`.
- Services expose `GET /healthz`, `GET /readyz`, and `GET /metrics`.
- Configuration is environment-driven; no hardcoded secrets.
- Contract changes require updates to `packages/event-contracts` and docs.

## Event Pipeline (v1)

- `telemetry-ingest` publishes `TelemetryFrameEvent` on `telemetry.frame.v1`.
- `telemetry-stream` consumes the subject and serves `/ws/telemetry` + `/ws/overlay`.
- `session-service` consumes and persists frame/session data for retrieval/export APIs.
- `analytics-service` consumes and updates per-session coaching/diagnostic snapshots.
- `device-gateway` consumes telemetry events and dispatches derived device signals through adapters.
