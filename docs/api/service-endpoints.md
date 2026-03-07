# Service Endpoints (v1)

## Telemetry Ingest
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/parser/schema`
- `GET /api/v1/ingest/stats`

## Telemetry Stream
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/streams/channels`
- `GET /api/v1/streams/stats`
- `GET /api/v1/streams/recent`
- `WS /ws/telemetry`
- `WS /ws/overlay`

## Session Service
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/laps`
- `GET /api/v1/sessions/{session_id}/frames`
- `GET /api/v1/sessions/{session_id}/export/json`
- `GET /api/v1/sessions/{session_id}/export/csv`

## Analytics Service
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/analysis/sessions/{session_id}`
- `GET /api/v1/analysis/laps/{lap_id}`
- `GET /api/v1/coaching/sessions/{session_id}`
- `GET /api/v1/diagnostics/sessions/{session_id}`
- `GET /api/v1/history/summary`

## Device Gateway
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/devices`
- `POST /api/v1/devices/test`
- `GET /api/v1/devices/status`
- `GET /api/v1/devices/adapters`
