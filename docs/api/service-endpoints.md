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
- `GET /api/v1/overlay/state`
- `WS /ws/telemetry`
- `WS /ws/overlay`

## Session Service
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

## Analytics Service
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/ingest/stats`
- `GET /api/v1/analysis/sessions/{session_id}`
  - includes `lap_count`, `best_lap_ms`, `consistency_score`
- `GET /api/v1/analysis/laps/{lap_id}?session_id=<optional>`
  - includes lap trace aggregates (`frame_count`, average/best speed, avg throttle/brake)
- `GET /api/v1/coaching/sessions/{session_id}`
  - ranked coaching messages with `rank`, `priority_score`, `repeat_count`
- `GET /api/v1/diagnostics/sessions/{session_id}`
  - diagnostics list plus replay-derived instability `zones`
- `GET /api/v1/history/summary`
  - includes best laps, average lap/session best, improvement trend, consistency, and session groupings

## Device Gateway
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/devices`
- `POST /api/v1/devices/test`
- `GET /api/v1/devices/status`
- `GET /api/v1/devices/adapters`
- `GET /api/v1/devices/events/recent`
- `GET /api/v1/devices/stats`
