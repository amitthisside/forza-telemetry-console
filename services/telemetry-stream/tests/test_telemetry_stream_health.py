from fastapi.testclient import TestClient
from telemetry_stream.main import app


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
