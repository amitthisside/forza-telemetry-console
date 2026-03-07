# analytics-service

FastAPI service that consumes telemetry frame events from NATS, derives session-level signals,
and serves analysis, coaching, diagnostics, and history endpoints.

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/ingest/stats`
- `GET /api/v1/analysis/sessions/{session_id}`
- `GET /api/v1/coaching/sessions/{session_id}`
- `GET /api/v1/diagnostics/sessions/{session_id}`
- `GET /api/v1/history/summary`
