# telemetry-ingest

FastAPI service that receives Forza UDP packets, decodes them via `forza-parser`, and publishes
`TelemetryFrameEvent` messages to NATS (`telemetry.frame.v1`).

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/parser/schema`
- `GET /api/v1/ingest/stats`

## Listener configuration

- `INGEST_BIND_HOST` (default `0.0.0.0`)
- `INGEST_BIND_PORT` (default `8443`)
