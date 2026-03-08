# Web Routes (MVP)

The `apps/web` frontend ships route-level views for all core PRD surfaces.

All routes render a shared top status bar with:
- Forza target endpoint (IP:port)
- ingest listener endpoint
- packet activity status and packet count

- `/`: Setup page (Forza stream IP/port + ingest listener status)
- `/live`: Live dashboard
- `/map`: Track map with replay scrub controls and color overlays
- `/analysis`: Session analysis summary (lap count, best lap, consistency, coaching/diagnostics counters)
- `/coaching`: Coaching suggestions view scaffold
- `/diagnostics`: Diagnostics + replay-derived instability zones
- `/history`: Historical analytics summary (best laps, averages, trend, consistency)
- `/devices`: Device adapter status/config view scaffold
- `/overlay/config`: Overlay widget visibility/config (local persistence)
- `/overlay`: OBS-facing overlay route using `/ws/overlay` low-latency feed

## Stream Source

The live dashboard attempts a WebSocket connection using:

- `VITE_STREAM_WS_URL` if set
- fallback `ws://localhost:8101/ws/telemetry`

The setup page reads ingest listener details from:

- `GET /api/v1/ingest/stats` (`telemetry-ingest`)

When no stream is available, the UI switches to simulated telemetry values so routes stay functional in local development.

## Map Data Source

The `/map` route reads replay data from `session-service`:

- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}/timeline`
- `GET /api/v1/sessions/{session_id}/track/path?color_by=speed|throttle|brake`
- `GET /api/v1/sessions/{session_id}/replay`

## Analysis/Diagnostics Data Source

The `/analysis` and `/diagnostics` routes read from both services:

- `GET /api/v1/sessions` (`session-service` session picker source)
- `GET /api/v1/analysis/sessions/{session_id}` (`analytics-service`)
- `GET /api/v1/diagnostics/sessions/{session_id}` (`analytics-service`)

## History Data Source

The `/history` route reads:

- `GET /api/v1/history/summary` (`analytics-service`)

## Overlay Data Source

The overlay surfaces read:

- `WS /ws/overlay` (`telemetry-stream`) for low-latency state
- `GET /api/v1/overlay/state` (`telemetry-stream`) as fallback/debug endpoint
- browser localStorage key `forza.overlay.config.v1` for widget visibility settings
