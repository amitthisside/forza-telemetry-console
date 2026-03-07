# Web Routes (MVP)

The `apps/web` frontend ships route-level views for all core PRD surfaces.

- `/`: Live dashboard
- `/map`: Track map with replay scrub controls and color overlays
- `/analysis`: Session analysis summary (lap count, best lap, consistency, coaching/diagnostics counters)
- `/coaching`: Coaching suggestions view scaffold
- `/diagnostics`: Diagnostics + replay-derived instability zones
- `/history`: Historical sessions view scaffold
- `/devices`: Device adapter status/config view scaffold
- `/overlay/config`: Overlay widget configuration view scaffold
- `/overlay`: OBS-facing overlay route preview

## Stream Source

The live dashboard attempts a WebSocket connection using:

- `VITE_STREAM_WS_URL` if set
- fallback `ws://localhost:8101/ws/telemetry`

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
