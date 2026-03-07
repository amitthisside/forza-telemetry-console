import os
from dataclasses import dataclass

from event_contracts import TELEMETRY_FRAME_SUBJECT


@dataclass(frozen=True)
class StreamSettings:
    nats_enabled: bool = True
    nats_url: str = "nats://nats:4222"
    telemetry_subject: str = TELEMETRY_FRAME_SUBJECT
    ring_buffer_size: int = 512
    subscriber_queue_size: int = 64

    @classmethod
    def from_env(cls) -> "StreamSettings":
        return cls(
            nats_enabled=os.getenv("STREAM_NATS_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            telemetry_subject=os.getenv("STREAM_TELEMETRY_SUBJECT", TELEMETRY_FRAME_SUBJECT),
            ring_buffer_size=int(os.getenv("STREAM_RING_BUFFER_SIZE", "512")),
            subscriber_queue_size=int(os.getenv("STREAM_SUBSCRIBER_QUEUE_SIZE", "64")),
        )
