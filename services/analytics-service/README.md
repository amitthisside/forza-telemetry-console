# analytics-service

FastAPI service that consumes telemetry frame events from NATS, derives session-level signals,
and serves analysis, coaching, diagnostics, and history endpoints.

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/ingest/stats`
- `GET /api/v1/analysis/sessions/{session_id}`
- `GET /api/v1/analysis/laps/{lap_id}?session_id=<optional>`
- `GET /api/v1/coaching/sessions/{session_id}`
- `GET /api/v1/diagnostics/sessions/{session_id}`
- `GET /api/v1/history/summary`

## Configuration

- `ANALYTICS_NATS_ENABLED` (default `true`)
- `NATS_URL` (default `nats://nats:4222`)
- `ANALYTICS_TELEMETRY_SUBJECT` (default event contract subject)
- `SESSION_SERVICE_BASE_URL` (default `http://session-service:8000`)

`SESSION_SERVICE_BASE_URL` is used to enrich analytics responses with lap and replay data from
`session-service`.
