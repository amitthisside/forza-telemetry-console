import os
from dataclasses import dataclass

from event_contracts import TELEMETRY_FRAME_SUBJECT


@dataclass(frozen=True)
class AnalyticsSettings:
    nats_enabled: bool = True
    nats_url: str = "nats://nats:4222"
    telemetry_subject: str = TELEMETRY_FRAME_SUBJECT
    session_service_base_url: str = "http://session-service:8000"

    @classmethod
    def from_env(cls) -> "AnalyticsSettings":
        return cls(
            nats_enabled=(
                os.getenv("ANALYTICS_NATS_ENABLED", "true").lower() in {"1", "true", "yes"}
            ),
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            telemetry_subject=os.getenv("ANALYTICS_TELEMETRY_SUBJECT", TELEMETRY_FRAME_SUBJECT),
            session_service_base_url=os.getenv(
                "SESSION_SERVICE_BASE_URL", "http://session-service:8000"
            ),
        )
