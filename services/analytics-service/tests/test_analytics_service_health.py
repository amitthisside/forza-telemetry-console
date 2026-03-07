from analytics_service.main import app
from fastapi.testclient import TestClient


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_history_summary_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/history/summary")
    assert response.status_code == 200
    assert response.json()["sessions"] == 0
