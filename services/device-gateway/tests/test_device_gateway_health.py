from device_gateway.main import app
from fastapi.testclient import TestClient


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_device_status_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/devices/status")
    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
