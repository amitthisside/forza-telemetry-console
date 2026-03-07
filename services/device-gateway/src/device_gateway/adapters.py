import json
import socket
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass
class DeviceEvent:
    event_id: str
    created_at: datetime
    session_id: str
    event_type: str
    severity: str
    payload: dict[str, float | int | str | bool | None] = field(default_factory=dict)


class DeviceAdapter(Protocol):
    name: str

    def send(self, event: DeviceEvent) -> None:
        ...


class SimulatedAdapter:
    name = "simulated"

    def __init__(self, capacity: int = 256) -> None:
        self.capacity = capacity
        self._recent: list[DeviceEvent] = []

    def send(self, event: DeviceEvent) -> None:
        self._recent.append(event)
        if len(self._recent) > self.capacity:
            self._recent.pop(0)

    def recent(self, limit: int = 20) -> list[DeviceEvent]:
        safe_limit = max(1, min(limit, self.capacity))
        return self._recent[-safe_limit:]


class UdpAdapter:
    name = "udp"

    def __init__(self, host: str, port: int) -> None:
        self._target = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, event: DeviceEvent) -> None:
        payload = json.dumps(
            {
                "event_id": event.event_id,
                "created_at": event.created_at.astimezone(UTC).isoformat(),
                "session_id": event.session_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "payload": event.payload,
            }
        ).encode("utf-8")
        self._sock.sendto(payload, self._target)


class SerialAdapter:
    name = "serial"

    def send(self, event: DeviceEvent) -> None:
        _ = event
        raise RuntimeError("serial adapter is not configured in this build")


@dataclass
class AdapterDispatchResult:
    delivered: int
    failed: int


class AdapterManager:
    def __init__(self, adapters: Sequence[DeviceAdapter]) -> None:
        self.adapters = list(adapters)

    def dispatch(self, event: DeviceEvent) -> AdapterDispatchResult:
        delivered = 0
        failed = 0
        for adapter in self.adapters:
            try:
                adapter.send(event)
                delivered += 1
            except Exception:
                failed += 1
        return AdapterDispatchResult(delivered=delivered, failed=failed)
