import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count

from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field

from device_gateway.adapters import (
    AdapterManager,
    DeviceEvent,
    SerialAdapter,
    SimulatedAdapter,
    UdpAdapter,
)
from device_gateway.config import DeviceGatewaySettings
from device_gateway.consumer import consume_telemetry_subject

settings = DeviceGatewaySettings.from_env()
logger = logging.getLogger(__name__)

simulated_adapter = SimulatedAdapter(capacity=512)
adapters = []
for adapter_name in settings.adapters:
    if adapter_name == "simulated":
        adapters.append(simulated_adapter)
    elif adapter_name == "udp":
        adapters.append(UdpAdapter(settings.udp_host, settings.udp_port))
    elif adapter_name == "serial":
        adapters.append(SerialAdapter())
adapter_manager = AdapterManager(adapters)

stop_event = asyncio.Event()
consumer_task: asyncio.Task[None] | None = None
event_counter = count(1)


@dataclass
class DeviceStats:
    telemetry_events_consumed: int = 0
    device_events_derived: int = 0
    adapter_deliveries: int = 0
    adapter_failures: int = 0


stats = DeviceStats()


class DeviceStatus(BaseModel):
    status: str


class DeviceAdapterStatus(BaseModel):
    configured: list[str]


class DeviceGatewayStats(BaseModel):
    telemetry_events_consumed: int
    device_events_derived: int
    adapter_deliveries: int
    adapter_failures: int


class DeviceEventPayload(BaseModel):
    event_id: str
    created_at: datetime
    session_id: str
    event_type: str
    severity: str
    payload: dict[str, float | int | str | bool | None] = Field(default_factory=dict)


class RecentDeviceEventsResponse(BaseModel):
    events: list[DeviceEventPayload]


def derive_device_events(event: TelemetryFrameEvent) -> list[DeviceEvent]:
    frame = event.frame
    now = datetime.now(UTC)
    derived: list[DeviceEvent] = []

    if frame.speed >= 220:
        derived.append(
            DeviceEvent(
                event_id=f"dev-{next(event_counter)}",
                created_at=now,
                session_id=event.session_id,
                event_type="speed.warning",
                severity="high",
                payload={"speed_kmh": round(frame.speed, 2)},
            )
        )

    rear_slip = max(frame.tire_slip.rl, frame.tire_slip.rr)
    if rear_slip >= 1.0:
        derived.append(
            DeviceEvent(
                event_id=f"dev-{next(event_counter)}",
                created_at=now,
                session_id=event.session_id,
                event_type="traction.warning",
                severity="medium",
                payload={"rear_slip": round(rear_slip, 3)},
            )
        )

    if frame.brake >= 0.85 and frame.speed >= 140:
        derived.append(
            DeviceEvent(
                event_id=f"dev-{next(event_counter)}",
                created_at=now,
                session_id=event.session_id,
                event_type="brake.heavy",
                severity="low",
                payload={"brake": round(frame.brake, 3), "speed_kmh": round(frame.speed, 2)},
            )
        )

    return derived


def process_telemetry_event(event: TelemetryFrameEvent) -> None:
    stats.telemetry_events_consumed += 1
    for device_event in derive_device_events(event):
        stats.device_events_derived += 1
        result = adapter_manager.dispatch(device_event)
        stats.adapter_deliveries += result.delivered
        stats.adapter_failures += result.failed
        if result.failed > 0:
            logger.warning(
                "adapter_dispatch_failed event_id=%s session_id=%s failed=%s",
                device_event.event_id,
                device_event.session_id,
                result.failed,
            )


@asynccontextmanager
async def lifespan(_: FastAPI):
    global consumer_task

    if settings.enabled and settings.nats_enabled:
        stop_event.clear()
        consumer_task = asyncio.create_task(
            consume_telemetry_subject(
                nats_url=settings.nats_url,
                subject=settings.telemetry_subject,
                on_event=process_telemetry_event,
                stop_event=stop_event,
            )
        )

    try:
        yield
    finally:
        if consumer_task is not None:
            stop_event.set()
            await consumer_task


app = FastAPI(title="device-gateway", version="0.1.0", lifespan=lifespan)
api = APIRouter(prefix="/api/v1")


@api.get("/devices")
def list_devices() -> dict[str, list[dict[str, str]]]:
    devices = [{"id": adapter.name, "status": "active"} for adapter in adapter_manager.adapters]
    return {
        "devices": devices
    }


@api.post("/devices/test")
def test_device_event() -> dict[str, str]:
    event = DeviceEvent(
        event_id=f"test-{next(event_counter)}",
        created_at=datetime.now(UTC),
        session_id="manual-test",
        event_type="manual.ping",
        severity="info",
        payload={"source": "api"},
    )
    result = adapter_manager.dispatch(event)
    stats.adapter_deliveries += result.delivered
    stats.adapter_failures += result.failed
    return {"status": "queued"}


@api.get("/devices/status", response_model=DeviceStatus)
def device_status() -> DeviceStatus:
    if not settings.enabled:
        return DeviceStatus(status="disabled")
    if stats.adapter_failures > 0:
        return DeviceStatus(status="degraded")
    return DeviceStatus(status="enabled")


@api.get("/devices/adapters", response_model=DeviceAdapterStatus)
def list_adapters() -> DeviceAdapterStatus:
    return DeviceAdapterStatus(configured=[adapter.name for adapter in adapter_manager.adapters])


@api.get("/devices/events/recent", response_model=RecentDeviceEventsResponse)
def recent_device_events(limit: int = 20) -> RecentDeviceEventsResponse:
    events = [
        DeviceEventPayload(
            event_id=event.event_id,
            created_at=event.created_at,
            session_id=event.session_id,
            event_type=event.event_type,
            severity=event.severity,
            payload=event.payload,
        )
        for event in simulated_adapter.recent(limit)
    ]
    return RecentDeviceEventsResponse(events=events)


@api.get("/devices/stats", response_model=DeviceGatewayStats)
def device_stats() -> DeviceGatewayStats:
    return DeviceGatewayStats(
        telemetry_events_consumed=stats.telemetry_events_consumed,
        device_events_derived=stats.device_events_derived,
        adapter_deliveries=stats.adapter_deliveries,
        adapter_failures=stats.adapter_failures,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    payload = "\n".join(
        [
            "# TYPE app_up gauge",
            "app_up 1",
            "# TYPE device_gateway_events_consumed_total counter",
            f"device_gateway_events_consumed_total {stats.telemetry_events_consumed}",
            "# TYPE device_gateway_events_derived_total counter",
            f"device_gateway_events_derived_total {stats.device_events_derived}",
            "# TYPE device_gateway_adapter_deliveries_total counter",
            f"device_gateway_adapter_deliveries_total {stats.adapter_deliveries}",
            "# TYPE device_gateway_adapter_failures_total counter",
            f"device_gateway_adapter_failures_total {stats.adapter_failures}",
        ]
    )
    return Response(content=f"{payload}\n", media_type="text/plain; version=0.0.4")


app.include_router(api)
