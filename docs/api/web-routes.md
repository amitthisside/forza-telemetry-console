# Web Routes (MVP)

The `apps/web` frontend currently ships route-level scaffolding for all PRD core views.

- `/`: Live dashboard
- `/map`: Track map view scaffold
- `/analysis`: Lap analysis view scaffold
- `/coaching`: Coaching suggestions view scaffold
- `/diagnostics`: Handling/traction diagnostics view scaffold
- `/history`: Historical sessions view scaffold
- `/devices`: Device adapter status/config view scaffold
- `/overlay/config`: Overlay widget configuration view scaffold
- `/overlay`: OBS-facing overlay route preview

## Stream Source

The live dashboard attempts a WebSocket connection using:

- `VITE_STREAM_WS_URL` if set
- fallback `ws://localhost:8101/ws/telemetry`

When no stream is available, the UI switches to simulated telemetry values so routes stay functional in local development.
