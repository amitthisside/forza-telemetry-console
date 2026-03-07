import os
from dataclasses import dataclass

from event_contracts import TELEMETRY_FRAME_SUBJECT


@dataclass(frozen=True)
class SessionSettings:
    database_url: str = "sqlite:///./forza_sessions.db"
    nats_enabled: bool = True
    nats_url: str = "nats://nats:4222"
    telemetry_subject: str = TELEMETRY_FRAME_SUBJECT

    @classmethod
    def from_env(cls) -> "SessionSettings":
        return cls(
            database_url=os.getenv("SESSION_DATABASE_URL", cls.database_url),
            nats_enabled=os.getenv("SESSION_NATS_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            telemetry_subject=os.getenv("SESSION_TELEMETRY_SUBJECT", TELEMETRY_FRAME_SUBJECT),
        )
