# Local Development Runbook

1. Copy `.env.example` to `.env`.
2. Run `make bootstrap`.
3. Run `make up`.
4. Verify health endpoints:
   - `http://localhost:8100/healthz` (`telemetry-ingest`)
   - `http://localhost:8101/healthz` (`telemetry-stream`)
   - `http://localhost:8102/healthz` (`session-service`)
   - `http://localhost:8103/healthz` (`analytics-service`)
   - `http://localhost:8104/healthz` (`device-gateway`)
5. Verify service telemetry pipeline stats:
   - `http://localhost:8100/api/v1/ingest/stats`
   - `http://localhost:8102/api/v1/ingest/stats`
   - `http://localhost:8103/api/v1/ingest/stats`
6. Open `http://localhost:3000` for frontend and `ws://localhost:8101/ws/telemetry` for live stream testing.
