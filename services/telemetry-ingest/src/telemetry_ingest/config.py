import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IngestSettings:
    bind_host: str = "0.0.0.0"
    bind_port: int = 5300
    udp_enabled: bool = True

    @classmethod
    def from_env(cls) -> "IngestSettings":
        return cls(
            bind_host=os.getenv("INGEST_BIND_HOST", "0.0.0.0"),
            bind_port=int(os.getenv("INGEST_BIND_PORT", "5300")),
            udp_enabled=os.getenv("INGEST_UDP_ENABLED", "true").lower() in {"1", "true", "yes"},
        )
