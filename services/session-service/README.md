# session-service

FastAPI service that consumes telemetry frame events from NATS and persists session/frame data.
Provides retrieval and export APIs for sessions.

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/ingest/stats`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/frames`
- `GET /api/v1/sessions/{session_id}/export/json`
- `GET /api/v1/sessions/{session_id}/export/csv`
