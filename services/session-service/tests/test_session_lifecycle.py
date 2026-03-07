from datetime import UTC, datetime
from uuid import uuid4

from event_contracts import TelemetryFrameEvent
from fastapi.testclient import TestClient
from session_service.main import app, process_telemetry_event
from telemetry_models import TelemetryFrame, Vector3


def _event(
    session_id: str,
    frame_index: int,
    lap_number: int | None,
    lap_distance: float | None,
    speed: float,
    throttle: float,
    brake: float,
    position_x: float,
    position_z: float,
    lap_time_ms: int | None = None,
) -> TelemetryFrameEvent:
    return TelemetryFrameEvent(
        event_id=f"evt-{uuid4().hex[:8]}",
        published_at=datetime.now(UTC),
        session_id=session_id,
        frame=TelemetryFrame(
            received_at=datetime.now(UTC),
            frame_index=frame_index,
            speed=speed,
            rpm=4200,
            throttle=throttle,
            brake=brake,
            lap_number=lap_number,
            lap_distance=lap_distance,
            lap_time_ms=lap_time_ms,
            world_position=Vector3(x=position_x, y=0.0, z=position_z),
        ),
    )


def test_lap_boundary_and_replay_apis() -> None:
    session_id = f"s-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        process_telemetry_event(_event(session_id, 1, 1, 120.0, 110.0, 0.8, 0.0, 10.0, 5.0))
        process_telemetry_event(_event(session_id, 2, 1, 620.0, 130.0, 0.9, 0.0, 30.0, 7.0))
        process_telemetry_event(_event(session_id, 3, 2, 80.0, 95.0, 0.4, 0.5, 50.0, 9.0, 90234))

        laps = client.get(f"/api/v1/sessions/{session_id}/laps").json()
        assert len(laps) >= 2
        assert laps[0]["lap_number"] == 1
        assert laps[1]["lap_number"] == 2

        replay = client.get(
            f"/api/v1/sessions/{session_id}/replay?start_frame=1&end_frame=3"
        ).json()
        assert replay["session_id"] == session_id
        assert len(replay["frames"]) == 3
        assert replay["frames"][2]["lap_id"] is not None

        timeline = client.get(f"/api/v1/sessions/{session_id}/timeline").json()
        assert timeline["frame_start"] == 1
        assert timeline["frame_end"] == 3
        assert timeline["frame_count"] == 3

        path = client.get(f"/api/v1/sessions/{session_id}/track/path?color_by=brake").json()
        assert path["color_by"] == "brake"
        assert len(path["points"]) == 3
        assert path["points"][2]["color_value"] == 0.5


def test_lap_boundary_fallback_from_distance_reset() -> None:
    session_id = f"s-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        process_telemetry_event(_event(session_id, 1, None, 650.0, 100.0, 0.6, 0.1, 0.0, 0.0))
        process_telemetry_event(_event(session_id, 2, None, 80.0, 90.0, 0.5, 0.2, 5.0, 1.0))

        laps = client.get(f"/api/v1/sessions/{session_id}/laps").json()
        assert len(laps) >= 2
        assert laps[0]["lap_number"] == 1
        assert laps[1]["lap_number"] == 2
