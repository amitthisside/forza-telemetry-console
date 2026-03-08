# Changelog

## 2026-03-08
- checkpoint: merged PR #4 (frontend MVP + CI/container stabilization)
- checkpoint: merged PR #5 (e2e telemetry pipeline + device gateway baseline)
- added Wave 1 backbone: session/lap lifecycle detection and replay/path/timeline APIs
- added Wave 2 major milestone: map route now renders replay path with color modes and scrub controls
- added Wave 3 major part: enriched analysis/coaching/diagnostics APIs plus analysis/diagnostics UI integrations
- added Wave 4 major part: historical analytics summary + overlay config persistence and low-latency overlay feed integration
- added Wave 5 closeout: operational counters/metrics for boundary detection, replay query performance, rule execution, and adapter dispatch failures
- added setup landing page (`/`) for Forza data stream IP/port entry and ingest listener visibility
- fixed compose UDP ingress wiring to honor `INGEST_BIND_PORT`/`INGEST_BIND_HOST` from `.env`
- fixed ingest container bind failure by forcing container bind host to `0.0.0.0` in compose
- corrected Forza Data Out decoding offsets (speed, gear, throttle, brake, lap/race timing fields)
- added global ingress status top bar across all routes with packet activity indicator
