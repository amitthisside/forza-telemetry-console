# Architecture Overview

The platform uses service boundaries aligned to ingest, stream fanout, persistence, analytics, and optional device output.

## Core Components

- Telemetry ingest over UDP in `telemetry-ingest`
- Event distribution over NATS (`telemetry.frame.v1`)
- Session persistence in `session-service` (SQLite in local dev)
- Real-time fanout in `telemetry-stream` via WebSocket
- Rule-based analytics in `analytics-service`
- React frontend and overlay routes in `apps/web`
- Kubernetes + Helm deployment model

## Runtime Flow

1. `telemetry-ingest` decodes Forza UDP packets into normalized telemetry frames.
2. Each frame is wrapped in `TelemetryFrameEvent` and published to NATS subject `telemetry.frame.v1`.
3. `telemetry-stream` consumes telemetry events and pushes frames to `/ws/telemetry` and `/ws/overlay`.
4. `session-service` consumes telemetry events and persists sessions + frame rows.
5. `analytics-service` consumes telemetry events, builds signal snapshots, and serves coaching/diagnostics APIs.
6. `device-gateway` consumes telemetry events and emits adapter-friendly device signals in isolated dispatch loops.
