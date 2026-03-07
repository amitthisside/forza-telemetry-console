# device-gateway

FastAPI service that consumes telemetry frame events and dispatches derived device signals
through pluggable adapters (`simulated`, `udp`, `serial`). Adapter failures are isolated from
core telemetry processing.

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/devices/status`
- `GET /api/v1/devices/adapters`
- `GET /api/v1/devices/events/recent`
- `GET /api/v1/devices/stats`
- `POST /api/v1/devices/test`

## Metrics highlights

`/metrics` includes event derivation totals and adapter dispatch delivery/failure counters.
