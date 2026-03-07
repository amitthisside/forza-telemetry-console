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


def test_history_summary_includes_trend_and_groupings(monkeypatch) -> None:
    async def fake_fetch_session_index():
        return [
            SimpleNamespace(
                session_id="s-1:track=spa:car=gt3",
                started_at="2026-03-01T00:00:00Z",
                ended_at="2026-03-01T00:20:00Z",
            ),
            SimpleNamespace(
                session_id="s-2:track=spa:car=gt3",
                started_at="2026-03-02T00:00:00Z",
                ended_at=None,
            ),
        ]

    async def fake_fetch_session_laps(session_id: str):
        if session_id.startswith("s-1"):
            return [
                SimpleNamespace(lap_id="s-1-lap-1", lap_number=1, lap_time_ms=94000),
                SimpleNamespace(lap_id="s-1-lap-2", lap_number=2, lap_time_ms=93000),
            ]
        return [
            SimpleNamespace(lap_id="s-2-lap-1", lap_number=1, lap_time_ms=91000),
            SimpleNamespace(lap_id="s-2-lap-2", lap_number=2, lap_time_ms=90000),
        ]

    monkeypatch.setattr("analytics_service.main.fetch_session_index", fake_fetch_session_index)
    monkeypatch.setattr("analytics_service.main.fetch_session_laps", fake_fetch_session_laps)

    client = TestClient(app)
    response = client.get("/api/v1/history/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["sessions"] == 2
    assert body["session_count_active"] == 1
    assert body["session_count_completed"] == 1
    assert body["best_lap_ms"] == 90000
    assert body["average_lap_ms"] == 92000.0
    assert body["improvement_trend_ms"] == 3000.0
    assert len(body["best_laps"]) == 4
    assert body["sessions_by_track"][0]["key"] == "spa"
    assert body["sessions_by_car"][0]["key"] == "gt3"
