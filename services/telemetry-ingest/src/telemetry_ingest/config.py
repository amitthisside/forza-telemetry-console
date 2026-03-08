import os
from dataclasses import dataclass

from event_contracts import TELEMETRY_FRAME_SUBJECT


@dataclass(frozen=True)
class IngestSettings:
    bind_host: str = "0.0.0.0"
    bind_port: int = 8443
    udp_enabled: bool = True
    nats_enabled: bool = True
    nats_url: str = "nats://nats:4222"
    telemetry_subject: str = TELEMETRY_FRAME_SUBJECT
    source: str = "telemetry-ingest"
    session_id: str = "local-session"

    @classmethod
    def from_env(cls) -> "IngestSettings":
        return cls(
            bind_host=os.getenv("INGEST_BIND_HOST", "0.0.0.0"),
            bind_port=int(os.getenv("INGEST_BIND_PORT", "8443")),
            udp_enabled=os.getenv("INGEST_UDP_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_enabled=os.getenv("INGEST_NATS_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            telemetry_subject=os.getenv("INGEST_TELEMETRY_SUBJECT", TELEMETRY_FRAME_SUBJECT),
            source=os.getenv("INGEST_SOURCE", "telemetry-ingest"),
            session_id=os.getenv("INGEST_SESSION_ID", "local-session"),
        )
