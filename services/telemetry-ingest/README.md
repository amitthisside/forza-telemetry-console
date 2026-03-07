# telemetry-ingest

FastAPI service that receives Forza UDP packets, decodes them via `forza-parser`, and publishes
`TelemetryFrameEvent` messages to NATS (`telemetry.frame.v1`).

## Key endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/parser/schema`
- `GET /api/v1/ingest/stats`
