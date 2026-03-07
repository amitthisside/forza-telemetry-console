from fastapi.testclient import TestClient
from telemetry_stream.main import app, publish_frame


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_stream_channels_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/streams/channels")
    assert response.status_code == 200
    assert "dashboard" in response.json()["channels"]


def test_stream_recent_and_stats_contract() -> None:
    publish_frame({"speed": 123.4, "rpm": 5000})

    client = TestClient(app)
    recent = client.get("/api/v1/streams/recent?limit=5")
    stats = client.get("/api/v1/streams/stats")

    assert recent.status_code == 200
    assert len(recent.json()["frames"]) >= 1
    assert stats.status_code == 200
    assert stats.json()["frames_ingested"] >= 1


def test_websocket_receives_connected_event() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as websocket:
        first = websocket.receive_json()
        assert first["type"] == "connected"
        assert first["channel"] == "telemetry"
