# Product Requirements Document
## Product Name
**Forza Telemetry Console**

## Document Version
v1.0

## Status
Draft for product and engineering alignment

---

# 1. Executive Summary

Forza Telemetry Console is a production-grade telemetry platform built specifically for **Forza telemetry data out**. It ingests live telemetry packets from Forza, parses and normalizes them, and powers a unified operator console for:

- real time dashboarding
- track map visualization
- session recording
- lap and driving analysis
- rule-based coaching
- hardware integration support
- stream overlay support
- vehicle behavior diagnostics
- historical performance analytics

The product is not intended to be a hobby dashboard. It is intended to be a polished, deployable system with a modular service-oriented backend, web frontend, persistent storage, observability, and cloud-native deployment support.

The system will initially support only **Forza telemetry output format** and will optimize deeply around that assumption.

---

# 2. Product Scope

## In scope
- Forza telemetry ingestion only
- Forza packet decoding and validation
- unified telemetry console
- live telemetry dashboard
- live track map
- session storage and replay-oriented persistence
- lap analysis and comparison
- rule-based coaching
- support layer for external hardware integrations
- stream overlay endpoints
- historical analytics
- microservice backend architecture
- Kubernetes deployment
- Helm chart packaging
- production observability and ops readiness

## Out of scope for v1
- support for any other racing game
- cloud multi-tenant SaaS
- native mobile apps
- user-to-user sharing or social features
- machine learning based coaching
- autonomous setup tuning engine
- marketplace/plugin ecosystem UI

---

# 3. Product Goals

## Primary goals
1. Build a production-ready telemetry platform specifically for Forza.
2. Deliver low-latency live telemetry visualization.
3. Provide meaningful post-session analysis and coaching.
4. Create a modular architecture that can be deployed locally or on Kubernetes.
5. Support future publishability as a polished product.

## Secondary goals
1. Enable optional external device support through adapters.
2. Support streamer workflows with browser-based overlays.
3. Provide a durable analytics foundation for future advanced features.

---

# 4. Target Users

## Primary users
- sim and arcade racing players who want deeper telemetry insight
- enthusiasts with multi-screen or desk setups
- streamers who want telemetry overlays
- technically inclined users who want external hardware support

## Secondary users
- advanced performance-oriented players who want historical analysis
- makers who want to connect LED, haptic, or serial devices

---

# 5. Product Principles

1. **Forza-first, not generic**  
   The product should be optimized for Forza telemetry and terminology rather than abstracting too early.

2. **Local-first but production-grade**  
   It should run well on a local machine, but architecture should not look like a toy app.

3. **Modular services**  
   Core capabilities should be separated into independently deployable services where appropriate.

4. **Low-latency experience**  
   Real-time telemetry must feel responsive.

5. **Operationally clean**  
   Logging, health checks, metrics, config management, and deployment workflows must be first-class.

6. **Extensible through contracts**  
   Hardware support and overlays should be powered by stable internal APIs and event contracts.

---

# 6. Functional Requirements

## 6.1 Live telemetry ingestion
The system must:
- receive Forza telemetry packets via UDP
- bind to configurable host and port
- validate packet size and format
- parse incoming packets into typed telemetry frames
- timestamp all frames on receipt
- reject malformed packets safely
- continue operating under packet loss or malformed input

## 6.2 Telemetry normalization
The system must expose a normalized internal Forza telemetry model including, at minimum:
- speed
- rpm
- gear
- throttle
- brake
- steering
- clutch if available in packet
- lap number
- lap time
- current race time
- lap distance if available
- world position x, y, z
- yaw, pitch, roll if available
- tire slip values
- wheel rotation speed if available
- suspension travel values
- acceleration values if available

## 6.3 Real-time dashboard
The product must provide a live dashboard displaying:
- speed
- RPM
- gear
- throttle and brake bars
- steering input
- lap timer
- delta indicator
- tire slip warnings
- traction/handling state summary
- session status

## 6.4 Track map
The product must:
- render a live vehicle position map based on Forza world coordinates
- reconstruct track path from recorded movement
- support coloring path segments by speed, throttle, or brake intensity
- support session replay on stored track path data

## 6.5 Session recording
The system must:
- record telemetry frames for every session
- identify session start and end
- identify lap boundaries
- store derived events
- persist session summaries
- support export in JSON and CSV

## 6.6 Driving analysis
The system must provide:
- lap-by-lap breakdown
- best lap comparison
- consistency analytics
- throttle trace analysis
- brake trace analysis
- corner entry and exit trend analysis where inferable
- event markers for wheelspin, heavy braking, and instability

## 6.7 Coaching
The system must provide a rule-based coaching module that:
- evaluates telemetry patterns
- emits suggestions with confidence or severity
- identifies repeated issues across laps
- prioritizes top issues per lap and per session

Example coaching outputs:
- braking too long before acceleration phase
- early throttle application causing rear slip
- inconsistent brake release across similar zones
- reduced exit speed compared to best lap trace

## 6.8 Hardware support layer
The platform must support optional hardware integrations via adapter interfaces.

Initial requirement is support architecture, not full device implementation.

The system must:
- expose telemetry-derived events
- support pluggable output adapters
- support serial or local network adapters
- provide simulated device mode for development
- isolate hardware failures from core telemetry services

## 6.9 Stream overlay
The system must provide:
- browser-renderable overlay endpoints
- low-latency telemetry-fed overlay components
- OBS-compatible UI routes
- configurable widget visibility

## 6.10 Diagnostics
The system must provide telemetry-driven diagnostic hints such as:
- suspected understeer trend
- suspected oversteer trend
- wheelspin intensity trend
- front or rear traction instability
- repeated instability zones

## 6.11 Historical analytics
The system must persist user performance history and expose:
- best laps
- average lap time by session
- improvement trend
- consistency scores
- session counts
- track and car statistics if identifiable from input or metadata

---

# 7. Non-Functional Requirements

## 7.1 Performance
- ingestion service must sustain at least 100 packets per second with headroom
- dashboard update path should target sub-100 ms visible latency
- websocket/event push should support at least 30 UI updates per second
- session recording must not block ingestion path

## 7.2 Reliability
- malformed packets must not crash the service
- downstream service failures must not crash ingestion
- temporary database failure should degrade gracefully where possible
- session data integrity must be maintained through orderly writes

## 7.3 Scalability
Although v1 is primarily single-user oriented, the architecture must support:
- scaling stateless services horizontally
- isolating ingest, analytics, and frontend concerns
- replacing SQLite with PostgreSQL without contract breakage
- adding event broker infrastructure if throughput grows

## 7.4 Security
- configuration secrets must not be hardcoded
- internal service traffic should be configurable for TLS in cluster environments
- admin or internal endpoints should be separated from public frontend routes
- container images should run as non-root where possible

## 7.5 Observability
- structured application logs required
- Prometheus-compatible metrics preferred
- liveness and readiness probes required
- distributed trace support optional but recommended

## 7.6 Maintainability
- services must have clear domain ownership
- API contracts must be versioned
- packet parser logic must be strongly tested
- configuration must be environment-driven

---

# 8. High-Level Architecture

The application will be built as a set of focused services.

## Core architectural style
- microservice-oriented backend
- event-driven communication where appropriate
- API-first service boundaries
- React-based frontend
- Kubernetes-native deployment model
- Helm-based packaging

## Proposed service topology

### 1. Telemetry Ingest Service
Responsibility:
- receive UDP packets from Forza
- parse and validate packet data
- emit normalized telemetry frames
- expose health and basic ingestion metrics

### 2. Telemetry Stream Service
Responsibility:
- fan out live telemetry to frontend clients
- manage websocket subscriptions
- optionally buffer recent telemetry frames
- expose stream channels for dashboard and overlays

### 3. Session Service
Responsibility:
- manage session lifecycle
- persist telemetry frames and lap metadata
- provide session retrieval APIs
- support exports

### 4. Analytics Service
Responsibility:
- derive events from telemetry
- compute lap summaries
- run coaching rules
- compute historical analytics and diagnostics

### 5. Overlay Service
Responsibility:
- serve optimized browser routes for stream overlays
- subscribe to live telemetry data
- provide minimal-latency overlay state

This can also be folded into the frontend app if preferred, but separating it is cleaner if overlay performance and independent deployment matter.

### 6. Frontend Web App
Responsibility:
- dashboard UI
- analysis UI
- history UI
- device config UI
- overlay config UI

### 7. Optional Device Gateway Service
Responsibility:
- hardware adapter runtime
- serial/network device communication
- event-driven output control

This should be separate so that device failures or OS-specific dependencies do not affect the core platform.

---

# 9. Suggested Communication Model

## Recommended internal pattern

### Ingestion to downstream
Prefer event-driven publishing from ingest to downstream consumers.

Two practical options:

### Option A: Redis-based event bus for v1
Use:
- Redis Pub/Sub or Redis Streams

Pros:
- simple
- fast to operationalize
- works well for small to mid deployment
- easy for local dev and Kubernetes

Recommended for v1.

### Option B: NATS for cleaner microservice messaging
Use:
- NATS subjects for telemetry and derived events

Pros:
- better service decoupling
- cleaner event-based architecture
- good performance and lightweight ops

If you want the architecture to feel more polished and production-serious from day one, **NATS is a strong choice**.

## Recommended decision
For a product-quality system, I would recommend:

- **NATS** for live message distribution
- **PostgreSQL** for persistent storage
- **Redis** only if needed for caching or ephemeral state

This gives a cleaner architecture than pushing everything through Redis.

---

# 10. Deployment Architecture

## Deployment targets
- local developer environment with Docker Compose
- single-node local Kubernetes cluster for testing
- production Kubernetes cluster

## Kubernetes requirements
Each service should have:
- Deployment
- Service
- ConfigMap
- Secret references where needed
- resource requests and limits
- liveness probe
- readiness probe
- pod disruption budget where useful
- ingress exposure where needed

## Helm packaging
A top-level Helm chart should deploy:
- frontend
- ingest service
- stream service
- session service
- analytics service
- optional device gateway
- NATS
- PostgreSQL
- optional Redis
- ingress definitions
- persistent volume claims for stateful dependencies

Helm values should support:
- local development settings
- staging settings
- production settings
- optional enable/disable for device gateway
- configurable image tags
- ingress hosts
- storage sizes
- database credentials via secret references

---

# 11. Infrastructure Design

## Recommended runtime stack

### Backend services
- Python 3.12+
- FastAPI for HTTP APIs
- asyncio for high-throughput networking
- pydantic for request/response and config models
- uvicorn or gunicorn+uvicorn workers as appropriate

### Frontend
- React
- TypeScript
- Vite or Next.js
- WebSocket client for real-time state
- charting via Recharts or lightweight canvas-based visualizations

### Messaging
- NATS

### Database
- PostgreSQL for production
- SQLite only for local single-binary or local prototype mode, not the default production design

### Caching / ephemeral state
- Redis optional

### Packaging
- Docker
- Kubernetes
- Helm

### Observability
- Prometheus metrics
- Grafana dashboards
- Loki or ELK for logs
- OpenTelemetry optional

---

# 12. Detailed Service Requirements

## 12.1 Telemetry Ingest Service

### Responsibilities
- open UDP listener
- receive raw Forza packets
- validate packet shape
- decode into internal frame schema
- assign server receipt timestamp
- publish live frame events to NATS
- optionally expose recent packet counters and parser error counters

### APIs
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /parser/schema` optional for introspection

### Scaling note
This service should generally run as a single active instance per telemetry input source unless you introduce source partitioning. Since a given Forza sender is pushing UDP to one endpoint, horizontal scaling here is not typical without a traffic distribution strategy.

### Special note
Kubernetes is not naturally ideal for arbitrary inbound UDP from a local game source unless network topology is planned. For publishable product packaging, it is often better to support:
- local Docker mode for game-to-app ingest
- Kubernetes deployment for internal components

If full Kubernetes deployment is desired for all services, ingress to UDP listener must be explicitly designed, such as:
- NodePort UDP service
- hostNetwork mode
- MetalLB LoadBalancer in local cluster
- direct host IP binding in dev environments

This is an important real-world constraint and should be called out in the PRD.

## 12.2 Telemetry Stream Service

### Responsibilities
- consume live telemetry events
- broadcast to subscribed clients over WebSocket
- maintain recent in-memory ring buffer
- support channel subscriptions for dashboard, overlay, and diagnostics preview

### APIs
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `WS /ws/telemetry`
- `WS /ws/overlay`

## 12.3 Session Service

### Responsibilities
- consume telemetry frames
- create or close sessions
- detect laps and derived boundaries
- persist frame data and lap summaries
- expose session retrieval APIs

### APIs
- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/laps`
- `GET /sessions/{session_id}/frames`
- `GET /sessions/{session_id}/export/json`
- `GET /sessions/{session_id}/export/csv`

## 12.4 Analytics Service

### Responsibilities
- consume telemetry and session events
- compute derived telemetry events
- run coaching rule engine
- compute diagnostics
- expose analysis APIs

### APIs
- `GET /analysis/sessions/{session_id}`
- `GET /analysis/laps/{lap_id}`
- `GET /coaching/sessions/{session_id}`
- `GET /diagnostics/sessions/{session_id}`
- `GET /history/summary`

## 12.5 Device Gateway Service

### Responsibilities
- subscribe to live telemetry-derived events
- load hardware adapters
- communicate with serial or network devices
- emit device status and errors
- support device simulation

### APIs
- `GET /devices`
- `POST /devices/test`
- `GET /devices/status`
- `GET /devices/adapters`

---

# 13. Data Model

## Primary persistent entities

### sessions
- id
- started_at
- ended_at
- source_ip
- source_port
- forza_packet_format_version if known
- metadata_json

### laps
- id
- session_id
- lap_number
- started_at
- ended_at
- lap_time_ms
- is_best
- summary_json

### telemetry_frames
- id
- session_id
- lap_id nullable
- received_at
- frame_index
- speed
- rpm
- gear
- throttle
- brake
- steering
- position_x
- position_y
- position_z
- yaw
- pitch
- roll
- tire_slip_fl
- tire_slip_fr
- tire_slip_rl
- tire_slip_rr
- suspension_fl
- suspension_fr
- suspension_rl
- suspension_rr
- raw_json or compact typed columns depending on design

### derived_events
- id
- session_id
- lap_id nullable
- event_type
- event_time
- severity
- payload_json

### coaching_messages
- id
- session_id
- lap_id nullable
- rule_id
- message
- severity
- confidence
- created_at

### diagnostics
- id
- session_id
- lap_id nullable
- diagnostic_type
- summary
- score
- payload_json

---

# 14. Storage Strategy

## Recommended production choice
Use PostgreSQL as the default production datastore.

Reason:
- strong query support
- mature Kubernetes support
- good JSON capabilities
- stable for historical analytics
- cleaner publishable architecture than SQLite for a multi-service product

## Data retention
Initial retention should be configurable:
- raw telemetry frames retention policy
- summarized analytics retention policy
- export support for archival

For local users, a default retention cap may be useful to avoid unbounded disk growth.

---

# 15. Frontend Requirements

## Main application views

### Live view
- speed, rpm, gear
- throttle/brake bars
- lap state
- delta and warnings
- telemetry health indicator

### Map view
- live map
- replay scrubbing for stored session
- color overlays by metric

### Analysis view
- lap list
- lap comparison
- trace graphs
- event markers

### Coaching view
- top issues this lap
- repeated session issues
- severity-ranked suggestions

### Diagnostics view
- traction and handling summaries
- instability trends

### History view
- sessions
- best laps
- trend graphs
- consistency scores

### Devices view
- adapter status
- connected devices
- test event triggers
- configuration controls

### Overlay config view
- choose overlay widgets
- size/layout presets
- OBS route preview

---

# 16. Technical Design Constraints

## Forza-only assumption
The parser, session model, rule engine, and UI language may all assume Forza telemetry semantics. No abstraction layer for multiple games is required in v1.

## UDP ingress in Kubernetes
This is a serious design consideration. Because the game sends UDP directly to the configured host and port:
- local desktop use may be easier with Docker Compose or direct host execution for the ingest service
- Kubernetes deployment requires explicit UDP exposure strategy
- if deployed on a local cluster, NodePort UDP or hostNetwork is likely required

This should not be hidden in the PRD. It is a real deployment concern.

## Time-series volume
Raw telemetry storage can grow quickly. The system should support:
- compression-friendly schema design
- retention controls
- optional downsampling for historical graphing

---

# 17. Scale Expectations

## Initial scale assumptions
For v1, assume:
- one active telemetry source per deployment
- one to five connected browser clients
- continuous telemetry sessions up to several hours
- low to moderate history volume

## Production-readiness expectations
Even if single-user, the platform should still support:
- clear service separation
- rolling updates
- crash recovery
- persistent storage
- image versioning
- environment-based config
- metrics and health endpoints

---

# 18. GitHub Organization and Repository Setup

For a serious product, do not keep this as a single messy repo without structure. You have two reasonable options.

## Option A: Monorepo under one GitHub org
Recommended for v1.

### GitHub org
Create an org, for example:
- `forza-telemetry-console`

### Repositories
#### 1. `platform`
Main monorepo containing:
- backend services
- frontend app
- shared API contracts
- infra manifests
- Helm chart
- local dev tooling
- docs

This is the best choice for fast coordinated development.

#### 2. `deployments` optional
Only if you want to separate environment-specific deployment overlays later.

#### 3. `docs` optional
Only if public docs, architecture docs, and website will become large.

## Option B: Polyrepo
Use only if you expect multiple engineers and independent release cycles very early.

Repos:
- `frontend-web`
- `service-ingest`
- `service-stream`
- `service-session`
- `service-analytics`
- `service-device-gateway`
- `helm-chart`
- `infra`
- `contracts`

This is cleaner at scale but creates more overhead early.

## Recommendation
Use a **monorepo** with strong internal boundaries.

---

# 19. Recommended Repository Structure

For a monorepo:

```text
platform/
  apps/
    web/
    overlay/
  services/
    telemetry-ingest/
    telemetry-stream/
    session-service/
    analytics-service/
    device-gateway/
  packages/
    forza-parser/
    telemetry-models/
    event-contracts/
    client-sdk/
  infra/
    docker/
    k8s/
    helm/
    scripts/
  docs/
    prd/
    architecture/
    runbooks/
    api/
  .github/
    workflows/
```

## Notes
- `forza-parser` should be its own package with strong tests
- `telemetry-models` should define shared schemas
- `event-contracts` should define NATS subjects and event payload models
- `client-sdk` can help frontend and internal service clients stay aligned

---

# 20. CI/CD Requirements

## GitHub Actions
At minimum, define workflows for:

### 1. Lint and test
- Python linting
- frontend linting
- unit tests
- parser contract tests

### 2. Build images
- build versioned Docker images for each service
- tag by commit SHA and semantic version

### 3. Security checks
- dependency vulnerability scanning
- container image scanning

### 4. Helm validation
- lint helm chart
- render manifests in CI

### 5. Integration tests
- bring up NATS, PostgreSQL, and services in CI
- run smoke tests across ingest to persistence path

### 6. Release pipeline
- publish versioned images
- publish Helm chart package
- optionally create GitHub release

---

# 21. Environment and Infrastructure Setup

## Environments
At minimum:
- local
- dev
- staging
- production

## Secrets management
Use:
- Kubernetes secrets for initial phase
- sealed secrets or external secrets later if needed

## Container registry
Use one of:
- GitHub Container Registry
- Docker Hub
- AWS ECR if hosted in AWS

Recommendation:
- **GitHub Container Registry** for simplicity if code is on GitHub

## Domain and ingress
If externally hosted:
- frontend ingress route
- API ingress route
- overlay route

Remember: UDP ingest is not a normal HTTP ingress problem and needs separate handling.

---

# 22. Helm Chart Design

## Chart structure
A parent chart should deploy subcharts or templates for:
- web frontend
- telemetry-ingest
- telemetry-stream
- session-service
- analytics-service
- device-gateway
- nats
- postgresql
- redis optional

## Values structure should include
- image repositories and tags
- replica counts
- service ports
- ingress enablement
- resource requests and limits
- database settings
- NATS settings
- retention policies
- feature toggles
- UDP ingest exposure mode:
  - hostNetwork
  - NodePort
  - disabled for remote-only mode

---

# 23. Testing Strategy

## Unit tests
- packet parser decoding
- telemetry normalization
- coaching rules
- diagnostics logic
- session boundary detection

## Integration tests
- ingest to NATS
- NATS to stream/session/analytics services
- persistence validation
- websocket live streaming behavior

## End-to-end tests
- synthetic Forza packet replay into ingest service
- UI validation on dashboard updates
- session persistence and retrieval
- overlay rendering

## Load tests
- sustained telemetry packet rates
- long session persistence
- multiple websocket clients

---

# 24. Open Product Decisions

These should be explicitly decided before engineering starts.

1. **Should overlay be a separate app or just a frontend route?**  
   Recommendation: frontend route first.

2. **Should device gateway ship enabled by default?**  
   Recommendation: no, feature-flagged.

3. **Should PostgreSQL be bundled in Helm by default?**  
   Recommendation: yes for self-hosted simplicity, but support external DB config.

4. **Should raw frame storage be fully enabled by default?**  
   Recommendation: yes with retention cap and optional downsampling.

5. **Should local desktop mode be first-class in addition to Kubernetes mode?**  
   Recommendation: yes, absolutely. Forza UDP ingress makes this important.

---

# 25. MVP Definition

A release qualifies as MVP only if it includes:

- working Forza UDP ingestion
- correct Forza packet parsing
- live dashboard
- live track map
- session storage
- lap analysis
- rule-based coaching
- historical analytics basics
- browser-based overlay
- Kubernetes deployment manifests
- Helm packaging
- CI pipeline
- observability basics
- production-grade docs and runbooks

That is a real product baseline, not just a prototype.

---

# 26. Risks

## 1. UDP ingress complexity in Kubernetes
This is probably the biggest infrastructure reality.

## 2. Telemetry parser correctness
If parsing is off, everything downstream becomes misleading.

## 3. Analytics credibility
Bad coaching or wrong diagnostics will reduce trust quickly.

## 4. Storage growth
Raw telemetry can become large over time.

## 5. Overengineering too early
Microservices should be real and useful, not complexity for its own sake.

---

# 27. Recommended Final Technical Direction

If this were my production recommendation, I would choose:

- Python backend services with FastAPI
- React + TypeScript frontend
- NATS for event distribution
- PostgreSQL for persistence
- optional Redis only if later needed
- Docker Compose for local-first run mode
- Kubernetes for cluster deployment
- Helm for packaging
- monorepo in a GitHub org
- GitHub Actions for CI/CD
- Prometheus metrics and structured logs from day one

This gives you a system that feels polished, serious, and publishable.

---

# 28. Final Recommendation on Architecture Shape

Even though you want microservices, I would keep the number of services disciplined.

Best v1 set:

- `telemetry-ingest`
- `telemetry-stream`
- `session-service`
- `analytics-service`
- `web`
- `device-gateway` optional

That is enough separation to be serious, without turning the platform into an ops burden.
