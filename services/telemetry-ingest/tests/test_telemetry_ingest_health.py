from fastapi.testclient import TestClient
from telemetry_ingest.main import app


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parser_schema_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/parser/schema")
    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "forza-telemetry-v1"
    assert body["minimum_packet_bytes"] == 64
