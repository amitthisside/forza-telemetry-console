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
- `GET /api/v1/sessions/{session_id}/laps`
- `GET /api/v1/sessions/{session_id}/frames`
- `GET /api/v1/sessions/{session_id}/replay`
- `GET /api/v1/sessions/{session_id}/track/path`
- `GET /api/v1/sessions/{session_id}/timeline`
- `GET /api/v1/sessions/{session_id}/export/json`
- `GET /api/v1/sessions/{session_id}/export/csv`

## Metrics highlights

`/metrics` includes:

- lap boundary transition counters
- inactive session closure counters
- replay query count/rows and average query latency
