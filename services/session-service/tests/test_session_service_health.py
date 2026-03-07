from fastapi.testclient import TestClient
from session_service.main import app


def test_healthz() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sessions_api_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_session_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/sessions/missing")
    assert response.status_code == 404


def test_csv_export_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/sessions/missing/export/csv")
    assert response.status_code == 404


def test_metrics_include_ops_counters() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "session_lap_boundary_transitions_total" in body
    assert "session_replay_queries_total" in body
