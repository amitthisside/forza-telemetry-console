import os
from dataclasses import dataclass

from event_contracts import TELEMETRY_FRAME_SUBJECT


@dataclass(frozen=True)
class DeviceGatewaySettings:
    enabled: bool = True
    nats_enabled: bool = True
    nats_url: str = "nats://nats:4222"
    telemetry_subject: str = TELEMETRY_FRAME_SUBJECT
    adapters: tuple[str, ...] = ("simulated",)
    udp_host: str = "127.0.0.1"
    udp_port: int = 49000

    @classmethod
    def from_env(cls) -> "DeviceGatewaySettings":
        raw_adapters = os.getenv("DEVICE_ADAPTERS", "simulated")
        adapters = tuple(a.strip() for a in raw_adapters.split(",") if a.strip())
        return cls(
            enabled=os.getenv("DEVICE_GATEWAY_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_enabled=os.getenv("DEVICE_NATS_ENABLED", "true").lower() in {"1", "true", "yes"},
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            telemetry_subject=os.getenv("DEVICE_TELEMETRY_SUBJECT", TELEMETRY_FRAME_SUBJECT),
            adapters=adapters or ("simulated",),
            udp_host=os.getenv("DEVICE_UDP_HOST", "127.0.0.1"),
            udp_port=int(os.getenv("DEVICE_UDP_PORT", "49000")),
        )
