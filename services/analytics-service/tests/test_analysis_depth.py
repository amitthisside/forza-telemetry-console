from types import SimpleNamespace

from analytics_service.main import ReplayFrame, app
from fastapi.testclient import TestClient


def test_session_analysis_includes_lap_metrics(monkeypatch) -> None:
    async def fake_fetch_session_laps(session_id: str):
        _ = session_id
        return [
            SimpleNamespace(lap_id="s-1-lap-1", lap_number=1, lap_time_ms=90000),
            SimpleNamespace(lap_id="s-1-lap-2", lap_number=2, lap_time_ms=93000),
        ]

    monkeypatch.setattr("analytics_service.main.fetch_session_laps", fake_fetch_session_laps)

    client = TestClient(app)
    response = client.get("/api/v1/analysis/sessions/s-1")
    assert response.status_code == 200
    body = response.json()
    assert body["lap_count"] == 2
    assert body["best_lap_ms"] == 90000


def test_lap_analysis_returns_trace_metrics(monkeypatch) -> None:
    async def fake_fetch_session_replay(session_id: str, limit: int = 5000):
        _ = session_id, limit
        return [
            ReplayFrame(
                frame_index=1,
                lap_id="s-1-lap-2",
                speed=120.0,
                throttle=0.7,
                brake=0.1,
                position_x=0.0,
                position_z=0.0,
            ),
            ReplayFrame(
                frame_index=2,
                lap_id="s-1-lap-2",
                speed=140.0,
                throttle=0.8,
                brake=0.2,
                position_x=5.0,
                position_z=5.0,
            ),
        ]

    monkeypatch.setattr("analytics_service.main.fetch_session_replay", fake_fetch_session_replay)

    client = TestClient(app)
    response = client.get("/api/v1/analysis/laps/s-1-lap-2")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["frame_count"] == 2
    assert body["best_speed_kmh"] == 140.0


def test_diagnostics_includes_zones(monkeypatch) -> None:
    async def fake_fetch_session_replay(session_id: str, limit: int = 5000):
        _ = session_id, limit
        return [
            ReplayFrame(
                frame_index=1,
                lap_id="s-1-lap-1",
                speed=150.0,
                throttle=0.5,
                brake=0.9,
                position_x=42.0,
                position_z=78.0,
            ),
            ReplayFrame(
                frame_index=2,
                lap_id="s-1-lap-1",
                speed=160.0,
                throttle=0.6,
                brake=0.92,
                position_x=39.0,
                position_z=81.0,
            ),
        ]

    monkeypatch.setattr("analytics_service.main.fetch_session_replay", fake_fetch_session_replay)

    client = TestClient(app)
    response = client.get("/api/v1/diagnostics/sessions/s-1")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["zones"], list)
    assert len(body["zones"]) >= 1
