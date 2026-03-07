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


def test_coaching_endpoint_emits_messages_for_signals() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/coaching/sessions/s-1"
        "?brake_release_variance=0.6&rear_slip_events=4&early_throttle_pct=0.7&exit_speed_delta_kmh=-8"
    )
    assert response.status_code == 200
    assert len(response.json()["messages"]) >= 2


def test_metrics_include_rule_counters() -> None:
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "analytics_coaching_rule_evaluations_total" in body
    assert "analytics_rule_evaluation_errors_total" in body
