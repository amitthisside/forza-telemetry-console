from datetime import UTC, datetime
from uuid import uuid4

from analytics_service.main import app, store
from event_contracts import TelemetryFrameEvent
from fastapi.testclient import TestClient
from telemetry_models import TelemetryFrame, WheelValues


def test_ingested_events_affect_analysis_endpoints() -> None:
    session_id = f"s-{uuid4().hex[:8]}"

    for frame_index in range(1, 5):
        event = TelemetryFrameEvent(
            event_id=f"evt-{uuid4().hex[:8]}",
            published_at=datetime.now(UTC),
            session_id=session_id,
            frame=TelemetryFrame(
                received_at=datetime.now(UTC),
                frame_index=frame_index,
                speed=90.0,
                throttle=0.8,
                brake=0.1,
                tire_slip=WheelValues(rl=1.2, rr=1.3),
            ),
        )
        store.ingest(event)

    client = TestClient(app)
    analysis = client.get(f"/api/v1/analysis/sessions/{session_id}").json()
    diagnostics = client.get(f"/api/v1/diagnostics/sessions/{session_id}").json()

    assert analysis["coaching_messages"] >= 1
    assert analysis["diagnostics"] >= 1
    assert len(diagnostics["diagnostics"]) >= 1
