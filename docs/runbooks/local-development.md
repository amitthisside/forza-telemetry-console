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
6. Open frontend routes:
   - `http://localhost:3000/`
   - `http://localhost:3000/map`
   - `http://localhost:3000/analysis`
   - `http://localhost:3000/coaching`
   - `http://localhost:3000/diagnostics`
   - `http://localhost:3000/history`
   - `http://localhost:3000/devices`
   - `http://localhost:3000/overlay/config`
   - `http://localhost:3000/overlay`
