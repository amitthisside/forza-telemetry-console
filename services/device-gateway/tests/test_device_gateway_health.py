from datetime import UTC, datetime

from device_gateway.main import app, process_telemetry_event, simulated_adapter
from event_contracts import TelemetryFrameEvent
from fastapi.testclient import TestClient
from telemetry_models import TelemetryFrame, WheelValues


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_device_status_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/devices/status")
    assert response.status_code == 200
    assert response.json()["status"] in {"enabled", "degraded", "disabled"}


def test_device_event_derivation_surfaces_recent_events() -> None:
    event = TelemetryFrameEvent(
        event_id="evt-1",
        published_at=datetime.now(UTC),
        session_id="s-1",
        frame=TelemetryFrame(
            received_at=datetime.now(UTC),
            frame_index=1,
            speed=230.0,
            brake=0.9,
            tire_slip=WheelValues(rl=1.2, rr=1.1),
        ),
    )
    process_telemetry_event(event)

    client = TestClient(app)
    response = client.get("/api/v1/devices/events/recent?limit=5")
    assert response.status_code == 200
    assert len(response.json()["events"]) >= 1

    recent = simulated_adapter.recent(5)
    assert len(recent) >= 1
