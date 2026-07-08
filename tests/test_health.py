"""Tests for the FastAPI application surface."""

from fastapi.testclient import TestClient

from dataops.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_health_ok():
    response = _client().get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_and_metrics():
    client = _client()

    assert client.get("/ready").json()["status"] == "ready"
    assert "pipelines_run" in client.get("/metrics").json()


def test_quality_validate_endpoint_flags_nulls():
    client = _client()
    payload = {
        "dataset": "users",
        "records": [{"id": 1}, {"id": None}],
        "rules": [{"name": "id_not_null", "rule_type": "not_null", "column": "id"}],
    }

    response = client.post("/quality/validate", json=payload)

    assert response.status_code == 200
    assert response.json()["passed"] is False
