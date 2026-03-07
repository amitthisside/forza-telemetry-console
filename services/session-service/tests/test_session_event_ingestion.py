from datetime import UTC, datetime
from uuid import uuid4

from event_contracts import TelemetryFrameEvent
from fastapi.testclient import TestClient
from session_service.main import app, process_telemetry_event
from telemetry_models import TelemetryFrame


def test_process_telemetry_event_persists_session_and_frame() -> None:
    session_id = f"s-{uuid4().hex[:8]}"
    event = TelemetryFrameEvent(
        event_id=f"evt-{uuid4().hex[:8]}",
        published_at=datetime.now(UTC),
        session_id=session_id,
        frame=TelemetryFrame(received_at=datetime.now(UTC), frame_index=1, speed=111.0, rpm=4500.0),
    )

    with TestClient(app) as client:
        process_telemetry_event(event)

        sessions = client.get("/api/v1/sessions").json()
        assert any(item["session_id"] == session_id for item in sessions)

        frames = client.get(f"/api/v1/sessions/{session_id}/frames").json()["frames"]
        assert len(frames) >= 1
        assert frames[0]["frame_index"] == 1
