# Architecture Overview

The platform uses service boundaries aligned to ingest, stream fanout, persistence, analytics, and optional device output.

## Core Components

- Telemetry ingest over UDP
- Event distribution over NATS
- PostgreSQL persistence for sessions and analytics
- React frontend and overlay routes
- Kubernetes + Helm deployment model
