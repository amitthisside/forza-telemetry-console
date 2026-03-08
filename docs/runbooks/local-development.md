# Local Development Runbook

1. Copy `.env.example` to `.env`.
2. Run `make bootstrap`.
3. Run `make up`.
4. Verify service health:
   - `http://localhost:8100/healthz` (telemetry-ingest)
   - `http://localhost:8101/healthz` (telemetry-stream)
   - `http://localhost:8102/healthz` (session-service)
   - `http://localhost:8103/healthz` (analytics-service)
   - `http://localhost:8104/healthz` (device-gateway)
5. Verify service telemetry pipeline stats:
   - `http://localhost:8100/api/v1/ingest/stats`
   - `http://localhost:8102/api/v1/ingest/stats`
   - `http://localhost:8103/api/v1/ingest/stats`
   - `http://localhost:8104/api/v1/devices/stats`
   - `http://localhost:8101/api/v1/overlay/state`
6. Verify replay/map APIs:
   - `http://localhost:8102/api/v1/sessions`
   - `http://localhost:8102/api/v1/sessions/<session_id>/timeline`
   - `http://localhost:8102/api/v1/sessions/<session_id>/track/path?color_by=speed`
   - `http://localhost:8102/api/v1/sessions/<session_id>/replay`
7. Verify analytics APIs (replace `<session_id>` and `<lap_id>`):
   - `http://localhost:8103/api/v1/analysis/sessions/<session_id>`
   - `http://localhost:8103/api/v1/analysis/laps/<lap_id>?session_id=<session_id>`
   - `http://localhost:8103/api/v1/coaching/sessions/<session_id>`
   - `http://localhost:8103/api/v1/diagnostics/sessions/<session_id>`
   - `http://localhost:8103/api/v1/history/summary`
8. Open frontend routes:
   - `http://localhost:3000/`
   - `http://localhost:3000/live`
   - `http://localhost:3000/map`
   - `http://localhost:3000/analysis`
   - `http://localhost:3000/coaching`
   - `http://localhost:3000/diagnostics`
   - `http://localhost:3000/history`
   - `http://localhost:3000/devices`
   - `http://localhost:3000/overlay/config`
   - `http://localhost:3000/overlay`

## Troubleshooting Quick Checks

- If lap/session boundaries look wrong, inspect `http://localhost:8102/metrics`:
  - `session_lap_boundary_transitions_total`
  - `session_inactive_closures_total`
- If replay/history queries feel slow, inspect `http://localhost:8102/metrics`:
  - `session_replay_queries_total`
  - `session_replay_query_avg_ms`
- If coaching/diagnostics volume drops unexpectedly, inspect `http://localhost:8103/metrics`:
  - `analytics_coaching_rule_evaluations_total`
  - `analytics_diagnostics_rule_evaluations_total`
  - `analytics_rule_evaluation_errors_total`
- If haptics/adapter dispatch fails, inspect `http://localhost:8104/metrics`:
  - `device_gateway_adapter_failures_total`

## Forza Stream Configuration

- Listener host/port for this machine are controlled by:
  - `INGEST_BIND_HOST` (default `0.0.0.0`)
  - `INGEST_BIND_PORT` (default `8443`)
- The web setup page (`/`) stores Forza target IP/port in browser localStorage key:
  - `forza.stream.config.v1`
